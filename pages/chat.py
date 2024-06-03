import streamlit as st
import pymysql
import boto3
import botocore
import openai
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import RetrievalQA
from botocore.client import Config
import create_db_embedding
from helper import generate_sql_sentence,generate_chat_response
from load_environment import load_environment


openai.api_key, aws_access_key_id, aws_secret_access_key, db_config = load_environment()

#Prompt Template
TEMPLATE = """ You are an expert SQL developer querying about User details. You have to write sql code in a SQL database based on a users question.

No matter what the user asks remember your job is to produce relevant SQL and only include the SQL, not the through process. So if a user asks to display something, you still should just p>
If you don't know the answer, provide what you think the sql should be but do not make up code if a column isn't available. You should be using '%' wildcard in the SQL queries.

As an example, a user will ask "Display the last 5 Users with Name Mathew?" The SQL to generate this would be:

SELECT *
FROM cr.PersonalInformation
WHERE Name LIKE '%Mathew%'
ORDER BY CandidateID DESC
LIMIT 5;

Another example, a user will ask "Display the Education details of the user with Name Mathew?" The SQL to generate this would be:
SELECT E.*
FROM cr.EducationalDetails AS E
JOIN cr.PersonalInformation AS P ON E.CandidateID = P.CandidateID
WHERE P.Name LIKE '%Mathew%';

Another example, a user will ask "name of the candidate who works at Company Name?" The SQL to generate this would be:
SELECT P.Name
FROM cr.PersonalInformation AS P
INNER JOIN cr.WorkExperiences AS W ON P.CandidateID = W.CandidateID
WHERE W.Company LIKE '%Company Name%';

Questions about User Personal Informatoin details fields should query cr.PersonalInformation
cr.PersonalInformation consists of CandidateID, Name, ContactNumber, EmailID, Location, JobTitle, DateOfBirth, Nationality, LanguagesKnown
CandidateID in the table cr.PersonalInformation

Questions about User Educational details fields should query cr.EducationalDetails
cr.EducationalDetails consists of Degree, Branch, CompletedYear, GPAOrPercentage, SchoolOrCollege, CandidateID
CandidateID is the FOREIGN KEY (CandidateID) REFERENCES PersonalInformation (CandidateID)

Questions about User Work Experiences details fields should query cr.WorkExperiences
cr.WorkExperiences consists of CandidateID, Company, Role, StartTime, EndTime, ExperienceInYears, KeyResponsibilities
CandidateID is the FOREIGN KEY (CandidateID) REFERENCES PersonalInformation (CandidateID)

Questions about User Experiences details fields should query cr.ExperienceDetails
cr.ExperienceDetails consists of CandidateID, OverallYearsofExperience, TechnicalSkill
CandidateID is the FOREIGN KEY (CandidateID) REFERENCES PersonalInformation (CandidateID)

Questions about User Certification details fields should query cr.Certification
cr.Certification consists of CandidateID, CertificateName, YearOfCertification, CertificateProvider, CertificateID
CandidateID is the FOREIGN KEY (CandidateID) REFERENCES PersonalInformation (CandidateID)

Questions about User Courses Completed details fields should query cr.CoursesCompleted
CoursesCompleted consists of CandidateID, CourseName, YearOfCourseCompletion, CourseProvider, CertificateID, TopicsCovered
CandidateID is the FOREIGN KEY (CandidateID) REFERENCES PersonalInformation (CandidateID)

Question: {question}
Context: {context}

SQL: ```sql ``` \n

"""
PROMPT = PromptTemplate(input_variables=["question", "context"], template=TEMPLATE, )

openai.api_key, aws_access_key_id, aws_secret_access_key, db_config = load_environment()

s3 = boto3.client('s3', config=Config(signature_version='s3v4'), region_name='ap-south-1', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)


def show_chat_page():
    st.subheader("ChatBot", divider="blue")
    expander = st.expander(":information_source:  :blue[**About**]")
    expander.info("""
        Welcome to our ChatBot, your AI-powered assistant for querying candidate information from our database. Here's what you can do with this ChatBot:

        - **Ask Questions**: You can have a natural language conversation with the ChatBot to query candidate details from our database. Simply ask questions, and the ChatBot will generate SQL queries to fetch the information you need.

        - **Example Prompts**: To get you started, here are some sample prompts:
            - "Give me the Name and Email of candidates who live in San Francisco in table."
            - "List the data engineers with 2+ years of experience in table."
            - "How can I contact Jennifer?"
            - "How many candidates are from Boston?"

        - **Retrieve Candidate Details**: The ChatBot will provide you with relevant candidate information based on your queries.

        - **View Table Data**: If you want to display a table of results, you have to ask the chatbot to show the results in a table

        Please keep in mind that this ChatBot is here to help you efficiently retrieve candidate information. If you have any questions or need further assistance, don't hesitate to ask.

        Thank you for using our ChatBot!
    """
    )


    #Connect to the MySQL database
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    cursor.execute('''SELECT CandidateID as 'Candidate ID',Name,ContactNumber as 'Contact Number',EmailID as 'Email ID',Location,JobTitle as 'Job Title',TimeStamp as 'Time Stamp' FROM cr.PersonalInformation''')
    data = cursor.fetchall()
    #st.markdown (''' # Candidates Details ''')
    df = pd.DataFrame(data, columns=['Candidate ID', 'Name', 'Contact Number', 'Email ID', 'Location', 'Job Title', 'Time Stamp'])
 
    api=openai.api_key
    create_db_embedding.create_embeddings(api)

    # Display Data
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.1,
        max_tokens=1000,
        openai_api_key=openai.api_key
    )
    def get_faiss():
        " get the loaded FAISS embeddings"
        embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
        return FAISS.load_local("faiss_index", embeddings)

    def sql_query(str_input):
        cursor.execute(str_input)
        data = cursor.fetchall()
        return data

    def fs_chain(question):
        """
        returns a question answer chain for faiss vectordb
        """
        docsearch = get_faiss()
        qa_chain = RetrievalQA.from_chain_type(llm,
                                            retriever=docsearch.as_retriever(),
                                            chain_type_kwargs={"prompt": PROMPT})
        return qa_chain({"query": question})

    def fs_chain1(str_input):
        """
        Performs QA capability for a question using SQL vector db store.
        Returns both SQL query result and generative response.
        """
        output = fs_chain(str_input)
        print(output)
        generative_response = None
        try:
            query_result = sql_query(output['result'])
            print(query_result)
            if len(query_result) > 0:
                # Convert the SQL result to a sentence
                sql_sentence = generate_sql_sentence(query_result)
                # Get generative response based on SQL sentence
                generative_response = generate_chat_response(sql_sentence, str_input)
                print(generative_response)
        except Exception as ex:
            generative_response = "Kindly rephrase your query, Unable to understand."
            print(Exception)
        return query_result, generative_response, output
    
    def extract_column_name(result_string):
        # Split the string by line and get the first line
        lines = result_string.split('\n')
        # Extract the column name from the first line (assuming it's in the "SELECT" statement)
        if lines[0].startswith("SELECT "):
            column_name = lines[0].replace("SELECT", "").strip().split(", ")
            return column_name
        else:
            return None
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"],avatar=message.get("avatar")):
            if message["role"] == "assistant" and "dataframe" in message:
                # Display the DataFrame in the chat
                st.dataframe(message["dataframe"])
            else:
                st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt, "avatar":"./static/user_icon.png" })
        # Display user message in chat message container
        with st.chat_message("user",avatar="./static/user_icon.png"):
            st.markdown(prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant",avatar="./static/ai_icon.png"):
            with st.spinner("Loading..."): 
                message_placeholder = st.empty()
                str_input = prompt
                response = fs_chain1(str_input)
                if "table" in str_input:
                    table_data = response[0]
                    v= response[2]
                    v2=v['result']
                    column_name = extract_column_name(v2)
                    if column_name:
                        # Assign the column name to the DataFrame
                        df = pd.DataFrame(table_data, columns=column_name)
                        st.dataframe(df)
                        message = {
                            "role": "assistant",
                            "content": f"**Assistant**: (Table)",
                            "dataframe": df,
                            "avatar" :"./static/ai_icon.png",
                        }
                        message_placeholder.markdown("")
                        st.session_state.messages.append(message)
                else:
                    generative_response1 = response[1]
                    message_placeholder.markdown(generative_response1)

                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": generative_response1, "avatar" :"./static/ai_icon.png"})
show_chat_page()