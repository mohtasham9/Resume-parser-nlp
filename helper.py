import streamlit as st
import base64, io
import openai
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import pymysql


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def extract_text_from_pdf(pdf_file_path):
    output_string = io.StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output_string, laparams=LAParams())
    with open(pdf_file_path, 'rb') as pdf_file:
        interpreter = PDFPageInterpreter(manager, converter)
        for page in PDFPage.get_pages(pdf_file, check_extractable=True):
            interpreter.process_page(page)
    converter.close()
    text = output_string.getvalue()
    output_string.close()
    
    # Remove blank lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    return '\n'.join(lines)


def extract_cv_details(resume_context, response_schema):
    """A prompt template to extract CV content in Json format."""
    delimitter = "####"
    system_message = f""" You are an intelligent talent recruiting professional. 
    You are required to read through the resume content provided between {delimitter} characters. 
    Your task is to extract key information from the resume content and answer in JSON format as mentioned in the function schema.
    For your reference, The current date is 17th october 2023. You should know the current date inorder to change "Present" or "Till Date" to current month and year.

        Please note the following specific requirements:
        - Whenever you encounter Skills in resume text, take that as a technical skills.
        - Date Of Birth should be in the format DD-MM-YYYY.
        - Please extract the city name as Location from the provided text. Remove country, state names from the text.
        - You should accurately extract and calculate the total work experience of the candidate. You should handle common variations in resume layouts, such as different date formats, section headers, and text structures.
        - You should identify and extract information related to work experiences, which may include job titles, company names, employment dates (start and end dates), and job descriptions. It should also account for different ways in which dates are presented, such as 'May 2018 - July 2020,' '05/2018 - 07/2020,' 'May 2021 - Present,' 'Aug 2020 - Till Date,' or 'May 2018 to July 2020.'
        - Whenever you encounter "Present" or "Till Date" under the work experience in the resume text, Please mention current month and year for the variable end_date under work experience.
        - You should be able to differentiate between different job roles, recognize gaps in employment, and accurately calculate the total duration of work experience, considering overlaps, internships, or part-time roles. Additionally, it should handle scenarios where candidates have multiple sections for work experiences, including different sections for full-time jobs, internships, or freelance work.

        Your responsibility is to evaluate and verify whether the extracted information is correct or not. Please refrain from providing any other information that is not explicitly requested.

        """
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimitter}{resume_context}{delimitter}"},
    ]
    functions = [
        {"name": "json_response", "parameters": response_schema}
    ]

    return messages, functions


def get_completion_from_messages(messages, functions=[], temperature=0.5, max_tokens=4000):
        """A function to get completion from provided messages using GPT models."""

        if len(functions) > 0:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo-16k',
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            response = openai.ChatCompletion.create(
                model=self.select_model(messages=messages, max_tokens=max_tokens),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return response


def execute_sql_query(connection, query, data):
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, data)
            connection.commit()
    except pymysql.Error as e:
        st.error(f"Database Error: {e}")

def generate_sql_sentence(sql_result):
    if isinstance(sql_result[0], int):
        # Handle the case when sql_result contains integers
        values = [str(value[0]) for value in sql_result]
    else:
        # Handle the case when sql_result contains tuples with names and other fields
        values = []
        for row in sql_result:
            # Assuming the first element is the name
            name = row[0]
            # If there are additional fields in the tuple, join them with a comma
            if len(row) > 0:
                other_fields = ', '.join(row[1:])
                values.append(f"{name} ({other_fields})")
            else:
                values.append(name)

    sentence = ", ".join(values)
    return sentence

def generate_chat_response(sql_sentence, str_input):
    # Generate a response using OpenAI chat model based on SQL sentence
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f'''You are an AI language model. 
         You have been given an SQL query result as input. 
         Your task is to convert this SQL query result into a meaningful sentence. Evaluate {str_input} and {sql_sentence}.
         Exclude the "SQL query result" words from the response '''}
    ]

    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            temperature=0.5,
            max_tokens=1000
        )

        generative_response = response.choices[0].message['content']
        return generative_response
    
    except openai.InvalidRequestError as e:
        st.error("PDF text exceeded token limit. Please upload a smaller file.")
        return