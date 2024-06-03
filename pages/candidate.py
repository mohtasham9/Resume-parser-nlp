# candidate_page.py

import streamlit as st
import boto3
import botocore
import os
import json
import openai
import pymysql
import pytz
import time
import base64
import datetime
from dateutil import parser
from dateutil.parser import parse
from json_schema import response_schema
from database import check_existing_candidate, cleanup_candidate_data
from load_environment import load_environment
from helper import extract_text_from_pdf, extract_cv_details, get_completion_from_messages, execute_sql_query, show_pdf
from pages.settings import (
    page_config,
    custom_css,
) 

page_config()
custom_css()

# Load credentials and settings
openai.api_key, aws_access_key_id, aws_secret_access_key, db_config = load_environment()

def show_candidate_page():   
    # Display subheader and information about the candidate section
    st.subheader("Candidate Section", divider="blue")
    expander = st.expander(":information_source:  :blue[**About**]")
    expander.info("""
        Talent-GPT is designed to help you easily upload your resume in PDF format and automatically extract essential candidate details from it. Here's what this application can do:

        - **Upload a Resume**: You can upload your resume in PDF format directly to the app.
        - **Resume Parsing**: The app will extract information such as your name, contact details, job title, educational background, work experience, technical skills, certifications, and more.
        - **Replace Previous Resumes**: When you upload a new PDF resume, it will replace the previous one, ensuring that the most recent information is considered.

        To get started, simply use the **"Upload your Resume"** section and let the app do the rest. It will analyze your resume and display the extracted information for your review.

        Thank you for using our Talent-GPT candidate information extraction tool!
    """ )

    # Initialize S3 client for AWS
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    # Create a directory to store uploaded resumes
    if not os.path.exists('./Resumes'):
        os.makedirs('./Resumes')

    # Allow the user to upload a PDF resume
    pdf_file = st.file_uploader("Upload your Resume", type=["pdf"])
    if pdf_file is not None:
        # Generate an S3 object key and save the uploaded resume locally
        s3_object_key = f'cr-resumegpt/{pdf_file.name}'
        save_image_path = './Resumes/' + pdf_file.name
        with open(save_image_path, "wb") as f:
            f.write(pdf_file.getbuffer())
        
        # Show the uploaded resume to the user
        show_pdf(save_image_path)
    
        # Extract details from the resume
        with st.spinner("Extracting details from the resume..."):
            try:
                resume_text = extract_text_from_pdf(save_image_path) 
                # Send the extracted text to OpenAI for analysis
                prompt, cv_details_schema = extract_cv_details(resume_context=resume_text, response_schema=response_schema)
                gpt_response = get_completion_from_messages(messages=prompt, functions=cv_details_schema)
                gpt_summary = gpt_response.choices[0].message.function_call.arguments
            except openai.InvalidRequestError as e:
                st.error("Please upload a smaller PDF file, the extracted text exceeded the token limit.")
                return

            if resume_text:
                response_data = json.loads(gpt_summary)
                try:
                    candidate_name = response_data['Personal_Information']['Name']
                    candidate_email = response_data['Personal_Information']['Email_ID']
                    experience_details = response_data.get('Experience_Details', {})
                    technical_skill = experience_details.get('Technical_Skills', [])
                except KeyError:
                    st.error("Please upload the correct resume.")
                    return

                existing_candidate_id = check_existing_candidate(candidate_name, candidate_email)
           
                if existing_candidate_id:
                    # Candidate with the same name and email exists, clean up the database
                    cleanup_candidate_data(existing_candidate_id)
                    candidate_id = existing_candidate_id
                else:
                    # Candidate does not exist, generate a new candidate ID
                    connection = pymysql.connect(**db_config)
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT MAX(CandidateID) from PersonalInformation")
                        last_candidate_id = cursor.fetchone()[0]

                    if last_candidate_id is not None:
                        candidate_id = last_candidate_id + 1
                    else:
                        candidate_id = 1

                if not candidate_name or not candidate_email or not technical_skill:
                        st.error("Unable to extract information from the given document.")
                        return
                else:
                    try:
                        if candidate_id:
                            # Rename the local PDF file to CandidateID.pdf
                            candidate_pdf_filename = f"{candidate_id}_{candidate_name}.pdf"
                            renamed_pdf_path = os.path.join('./Resumes', candidate_pdf_filename)
                            # Rename the file
                            os.rename(save_image_path, renamed_pdf_path)
                            s3.upload_file(renamed_pdf_path, 'cr-resumegpt', f'cr-resumegpt/{candidate_pdf_filename}')
                            os.remove(renamed_pdf_path)
                    except botocore.exceptions.NoCredentialsError:
                        st.error("AWS credentials not found. Please provide AWS access key and secret key.")

                connection = pymysql.connect(**db_config)

                date_of_birth = response_data['Personal_Information'].get('Date_of_Birth')
                if date_of_birth == '':
                    date_of_birth = None  # Set to None if Date_of_Birth is empty
                else:
                    try:
                        date_of_birth = parser.parse(date_of_birth).date()
                    except ValueError:
                        # Handle parsing error (e.g., invalid date format)
                        date_of_birth = None
                ts = time.time()
                ist = pytz.timezone('Asia/Kolkata')
                cur_date = datetime.datetime.fromtimestamp(ts, ist).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts, ist).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)
                personal_data = {
                    'CandidateID': candidate_id,
                    'Name': response_data['Personal_Information']['Name'],
                    'ContactNumber': response_data['Personal_Information']['Contact_Number'],
                    'EmailID': response_data['Personal_Information']['Email_ID'],
                    'Location': response_data['Personal_Information']['Location'],
                    'JobTitle': response_data['Personal_Information']['Job_Title'],
                    'DateOfBirth': date_of_birth,
                    'Nationality': response_data['Personal_Information'].get('Nationality', None),  # Provide a default value or None
                    'LanguagesKnown': ', '.join(response_data['Personal_Information']['Languages_Known']),
                    'TimeStamp':timestamp
                }
                insert_personal_query = """
                    INSERT INTO PersonalInformation (CandidateID, Name, ContactNumber, EmailID, Location, JobTitle, DateOfBirth, Nationality, LanguagesKnown, TimeStamp)
                    VALUES (%(CandidateID)s, %(Name)s, %(ContactNumber)s, %(EmailID)s, %(Location)s, %(JobTitle)s, %(DateOfBirth)s, %(Nationality)s, %(LanguagesKnown)s, %(TimeStamp)s)
                """
                execute_sql_query(connection, insert_personal_query, personal_data)

                educational_details = response_data.get('Educational_Details',[])

                for educational_detail in educational_details:
                    try:
                        gpa_or_percentage = float(educational_detail['GPA_or_Percentage'])
                    except ValueError:
                        gpa_or_percentage = None  # Handle invalid values gracefully

                    educational_data = {
                                'Degree': educational_detail['Degree'],
                                'Branch': educational_detail['Branch'],
                                'CompletedYear': educational_detail['Completed_Year'],
                                'GPAOrPercentage': gpa_or_percentage,
                                'SchoolOrCollege': educational_detail['School_or_College'],
                                'CandidateID': candidate_id
                            }
                    insert_educational_query = """
                        INSERT INTO EducationalDetails (Degree, Branch, CompletedYear, GPAOrPercentage, SchoolOrCollege, CandidateID)
                        VALUES (%(Degree)s, %(Branch)s, %(CompletedYear)s, %(GPAOrPercentage)s, %(SchoolOrCollege)s, %(CandidateID)s)
                    """
                    execute_sql_query(connection, insert_educational_query, educational_data)

                # Extract the Experience_Details from the JSON data
                experience_details = response_data.get('Experience_Details', {})

                # Extract the Overall_years_of_experience and Technical_Skills
                overall_years_of_experience = experience_details.get('Overall_years_of_experience', None)
                technical_skill = experience_details.get('Technical_Skills', [])

                # Insert the Experience_Details into the "ExperienceDetails" table
                experience_details_data = {
                    'CandidateID': candidate_id,
                    'OverallYearsOfExperience': overall_years_of_experience,
                    'TechnicalSkill': ', '.join(technical_skill)  # Convert the list to a comma-separated string
                }
                insert_experience_details_query = """
                    INSERT INTO ExperienceDetails (CandidateID, OverallYearsOfExperience, TechnicalSkill)
                    VALUES (%(CandidateID)s, %(OverallYearsOfExperience)s, %(TechnicalSkill)s)
                """
                execute_sql_query(connection, insert_experience_details_query, experience_details_data)
                work_experiences = response_data.get('Work_Experiences', [])

                for work_experience in work_experiences:
                    start_time = work_experience['Start_time']
                    end_time = work_experience['End_time']

                    # Convert start_time and end_time to DATE format (e.g., 'Feb, 2023' to '2023-02-01')
                    try:
                        start_time_date = parse(start_time).date()
                    except ValueError:
                        start_time_date = None  # Handle parsing error gracefully

                    # Check if end_time is "current organization" and replace it with the current Month, YYYY
                    if end_time.lower() == "current organization":
                        end_time_date = datetime.now().date()
                    else:
                        try:
                            end_time_date = parse(end_time).date()
                        except ValueError:
                            end_time_date = None  # Handle parsing error gracefully
                    # Calculate experience_in_years as the difference between end_time and start_time
                    if start_time_date and end_time_date:
                        experience_in_years = (end_time_date - start_time_date).days // 365
                    else:
                        experience_in_years = None  # Handle cases where dates are not valid

                    work_experience_data = {
                        'CandidateID': candidate_id,
                        'Company': work_experience['Company'],
                        'Role': work_experience['Role'],
                        'StartTime': start_time_date,
                        'EndTime': end_time_date,
                        'ExperienceInYears': experience_in_years,
                        'KeyResponsibilities': work_experience['Key_Responsibilities']
                    }

                    # Insert the work experience data into the "WorkExperiences" table
                    insert_work_experience_query = """
                        INSERT INTO WorkExperiences (CandidateID, Company, Role, StartTime, EndTime, ExperienceInYears, KeyResponsibilities)
                        VALUES (%(CandidateID)s, %(Company)s, %(Role)s, %(StartTime)s, %(EndTime)s, %(ExperienceInYears)s, %(KeyResponsibilities)s)
                    """
                    execute_sql_query(connection, insert_work_experience_query, work_experience_data)
                certifications = response_data.get('Certifications', [])
                for certification in certifications:
                    certificate_name = certification.get('Certificate_Name', '')
                    year_of_certification = certification.get('Year_of_Certification', '')
                    certificate_provider = certification.get('Certificate_Provider', '')
                    certificate_id = certification.get('Certificate_ID', ''),
                    skill_covered = certification.get('Skills_Covered','')
                    certification_data = {
                        'CandidateID': candidate_id,
                        'CertificateName': certificate_name,
                        'YearOfCertification': year_of_certification,
                        'CertificateProvider': certificate_provider,
                        'CertificateID': certificate_id,
                        'SkillsCovered': skill_covered
                    }
                    # Insert the certification data into the "Certification" table
                    insert_certification_query = """
                        INSERT INTO Certification (CandidateID, CertificateName, YearOfCertification, CertificateProvider, CertificateID, SkillsCovered)
                        VALUES (%(CandidateID)s, %(CertificateName)s, %(YearOfCertification)s, %(CertificateProvider)s, %(CertificateID)s, %(SkillsCovered)s)
                    """
                    execute_sql_query(connection, insert_certification_query, certification_data)
                coursescompleteds = response_data.get('Courses_Completed',[])
                for coursescompleted in coursescompleteds:
                    course_name = coursescompleted.get('Course_Name','')
                    year_of_course_completion = coursescompleted.get('Year_of_Course_Completion','')
                    course_provider = coursescompleted.get('Course_Provider','')
                    course_certificate_id = coursescompleted.get('Certificate_ID','')
                    topics_covered = coursescompleted.get('Topics_Covered','')
                    coursescompleted_data = {
                        'CandidateID': candidate_id,
                        'CourseName': course_name,
                        'YearOfCourseCompletion': year_of_course_completion,
                        'CourseProvider': course_provider,
                        'CertificateID': course_certificate_id,
                        'TopicsCovered': topics_covered,
                    }
                    # Insert the courses completed data into the "CoursesCompleted" table
                    insert_coursescompleted_query = """
                        INSERT INTO CoursesCompleted (CandidateID, CourseName, YearOfCourseCompletion, CourseProvider, CertificateID, TopicsCovered)
                        VALUES (%(CandidateID)s, %(CourseName)s, %(YearOfCourseCompletion)s, %(CourseProvider)s, %(CertificateID)s, %(TopicsCovered)s)
                    """
                    execute_sql_query(connection, insert_coursescompleted_query, coursescompleted_data)
                st.header("**Resume Analysis**", divider="blue")
                st.success("Hello " + response_data['Personal_Information']['Name'])
                st.subheader("**Your Basic info**", divider="blue")
                overall_years_of_experience = response_data["Experience_Details"]["Overall_years_of_experience"]
                technical_skills = response_data["Experience_Details"]["Technical_Skills"]
                try:
                    st.markdown('Name: **{}**'.format(response_data['Personal_Information']['Name']))
                    st.markdown('Email: **{}**'.format(response_data['Personal_Information']['Email_ID']))
                    st.markdown('Contact: **{}**'.format(response_data['Personal_Information']['Contact_Number']))
                    st.markdown('Job Title: **{}**'.format(response_data['Personal_Information']['Job_Title']))
                    educational_details = response_data['Educational_Details']
                    highest_degree = max(educational_details, key=lambda x: x['Degree'])
                    st.markdown('Highest Degree: **{}**'.format(highest_degree['Degree']))
                    st.markdown('Overall Years of Experience: **{}**'.format(overall_years_of_experience))
                    st.markdown('Technical skills: **{}**'.format(', '.join(technical_skills)))
                except:
                    pass
            else:
                st.error('Unable to extract information from the resume.')
show_candidate_page()