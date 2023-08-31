import streamlit as st
import nltk
import spacy
nltk.download('stopwords')
spacy.load('en_core_web_sm')

import os
import openai
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS, Pinecone
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from llama_index import SQLDatabase,ServiceContext
from llama_index.llms import OpenAI
from sqlalchemy import select, create_engine, MetaData, Table,inspect
from llama_index.indices.struct_store.sql_query import NLSQLTableQueryEngine
from IPython.display import Markdown, display
import pandas as pd
import base64, random
import time, datetime
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io, random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
import pafy
import plotly.express as px
from dotenv import load_dotenv
load_dotenv()


openai.api_key = os.environ.get('OPENAI_API_KEY')

db_user = "root"
db_password = "admin" #Enter you password database password here
db_host = "localhost"  
db_name = "sra" #name of the database
db_port = "3306" #specify your port here
connection_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

connection = pymysql.connect(host='localhost', user='root', password='admin')
cursor = connection.cursor()

TEMPLATE = """ You are an expert SQL developer querying about User details. You have to write sql code in a SQL database based on a users question.
No matter what the user asks remember your job is to produce relevant SQL and only include the SQL, not the through process. So if a user asks to display something, you still should just produce SQL.
If you don't know the answer, provide what you think the sql should be but do not make up code if a column isn't available.

 
As an example, a user will ask "Display the last 5 Users with Name Mathew?" The SQL to generate this would be:

 
select * from sra.user_data where Name = "Mathew"
limit 5;

 
Questions about User details fields should query sra.user_data
sra.user_data consists of Name, Email_ID, Timestamp and Actual_skills

 
Question: {question}
Context: {context}
 
SQL: ```sql ``` \n

"""
PROMPT = PromptTemplate(input_variables=["question", "context"], template=TEMPLATE, )

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
    performs qa capability for a question using sql vector db store
    the prompts.fs_chain is used but with caching
    """
    output = fs_chain(str_input)
    return output

# adding this to test out caching
@st.cache_data(ttl=86400)
def sf_query(str_input):
    cursor.execute(str_input)
    data = cursor.fetchall()
    return data

def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)



def insert_data(name, email, timestamp, no_of_pages, skills):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s)"""
    rec_values = (
    name, email, timestamp, str(no_of_pages), skills)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


st.set_page_config(
    page_title="Resume Analyzer",
    page_icon='./Logo/SRA_Logo.ico',
)


def run():
    st.title("Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)
    connection.select_db("sra")

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Actual_skills VARCHAR(1024) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    if choice == 'Normal User':
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smart recommendation based on it."</h4>''',
        #             unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                    st.text('Skills:' + str(resume_data['skills']))
                   # st.text('Total Experience:' + str(resume_data['total_experience']))
                except:
                    pass
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)
                insert_data(resume_data['name'], resume_data['email'],  timestamp,
                            str(resume_data['no_of_pages']), str(resume_data['skills']),
                            )
                connection.commit()
            else:
                st.error('Something went wrong..')
    else:
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')
        # Display Data
        cursor.execute('''SELECT*FROM user_data''')
        data = cursor.fetchall()
        st.header("**User's👨‍💻 Data**")
        df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Timestamp', 'Total Page', 'Actual Skills'])
        st.dataframe(df)
        st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
        # Chat input field
        # st.header("**ChatBot Assistant**")
        # chat_input = st.text_area("Enter your query:", "")

        str_input = st.text_input(label='What would you like to answer? (e.g. How many candidates with skills java and C++?)')

        if len(str_input) > 1:
            with st.spinner('Looking up your question in Database now...'):
                try:
                    output = fs_chain1(str_input)
                    #st.write(output)
                    try:
                        # if the output doesn't work we will try one additional attempt to fix it
                        query_result = sf_query(output['result'])
                        if len(query_result) > 1:
                            st.write(query_result)
                            st.write(output)
                        else:
                            st.write("No query result found.")
                    except Exception as ex:
                        st.write("An error occurred while querying the database.")
                        st.write(str(ex))
                except Exception as ex:
                    st.write("An error occurred while processing your query.")
                    st.write(str(ex))         
run()
