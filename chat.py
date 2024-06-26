import streamlit as st
import pymysql
import boto3
import botocore
import openai
import pandas as pd
from dataclasses import dataclass
from typing import Literal
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import RetrievalQA
from botocore.client import Config
import create_db_embedding
from helper import generate_sql_sentence,generate_chat_response
from load_environment import load_environment
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder


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
    st.subheader("ChatBot")
    expander = st.expander("See explanation")
    expander.info("""
            ### About:
            - This section is for the internal user who wants to query about a candidate.
            - User can have a conventional chat. 
            ### Sample Prompts:
            - ​Give Name, Email of candidates who lives in San Francisco.
            - List the data engineers with 2+ years of experience.
            - How can I contact Jennifer?
            - How many candidates are from Boston?
    """
    )

    #Connect to the MySQL database
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    cursor.execute('''SELECT CandidateID as 'Candidate ID',Name,ContactNumber as 'Contact Number',EmailID as 'Email ID',Location,JobTitle as 'Job Title',TimeStamp as 'Time Stamp' FROM cr.PersonalInformation''')
    data = cursor.fetchall()
    st.markdown (''' # Candidates Details ''')
    df = pd.DataFrame(data, columns=['Candidate ID', 'Name', 'Contact Number', 'Email ID', 'Location', 'Job Title', 'Time Stamp'])

    @st.cache_data
    def generate_download_links(df):
        def generate_link(row):
            candidateid = row['Candidate ID']
            candidatename=row['Name']
            pdf_file_name = f"cr-resumegpt/{candidateid}_{candidatename}.pdf"
            pdf_file_url = s3.generate_presigned_url('get_object', Params={'Bucket': 'cr-resumegpt', 'Key': pdf_file_name}, ExpiresIn=3600)
            return pdf_file_url
        return df.apply(generate_link, axis=1)

    # Generate download links and add the 'Resume' column to the DataFrame
    df['Resume'] = generate_download_links(df)

    gd=GridOptionsBuilder.from_dataframe(df)
    gd.configure_column("Resume",
        cellRenderer=JsCode("""
                    class UrlCellRenderer {
                    init(params) {
                        this.eGui = document.createElement('a');
                        this.eGui.innerText = 'Download';
                        this.eGui.setAttribute('href', params.value);
                        this.eGui.setAttribute('style', "text-decoration:none");
                        this.eGui.setAttribute('target', "_blank");
                    }
                    getGui() {
                        return this.eGui;
                    }
                    }
                """)
    )
    gd.configure_pagination(enabled=True, paginationAutoPageSize=True)
    gd.configure_side_bar()
    gridoptions = gd.build()
    AgGrid(df, gridOptions=gridoptions,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        height=500,
        custom_css={
                    "#gridToolBar": {
                        "padding-bottom": "0px !important",
                    }
                },
        fit_columns_on_grid_load=True)
    @dataclass
    class Message:
        """Class for keeping track of a chat message."""
        origin: Literal["human", "ai"]
        message: str

    def load_css():
        with open("static/styles.css", "r") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)

    def initialize_session_state():
        if "history" not in st.session_state:
            st.session_state.history = []

    def on_click_callback():
        with get_openai_callback() as cb:
            human_prompt = st.session_state.human_prompt
            str_input = human_prompt
            generative_response1 = fs_chain1(str_input)
            llm_response = generative_response1
            st.session_state.history.append(
                Message("human", human_prompt)
            )
            st.session_state.history.append(
                Message("ai", llm_response)
            )
    
    load_css()
    initialize_session_state()

    chat_placeholder = st.container()
    prompt_placeholder = st.form("chat-form")

    with chat_placeholder:
        for chat in st.session_state.history:
            div = f"""
                    <div class="chat-row 
                        {'' if chat.origin == 'ai' else 'row-reverse'}">
                        <img class="chat-icon" src="app/static/{
                            'ai_icon.png' if chat.origin == 'ai' 
                                        else 'user_icon.png'}"
                            width=32 height=32>
                        <div class="chat-bubble
                        {'ai-bubble' if chat.origin == 'ai' else 'human-bubble'}">
                            &#8203;{chat.message}
                        </div>
                    </div>
                        """
            st.markdown(div, unsafe_allow_html=True)
        
        for _ in range(3):
            st.markdown("")
    
    with prompt_placeholder:
        st.markdown("**Enter Your Query**")
        cols = st.columns((6, 1))
        cols[0].text_input(
            "Chat",
            label_visibility="collapsed",
            key="human_prompt",
        )
        cols[1].form_submit_button(
            "Submit", 
            type="primary", 
            on_click=on_click_callback, 
        )

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
        return generative_response
show_chat_page()