# recruiter_page.py

import streamlit as st
import matplotlib.pyplot as plt
import pymysql
import boto3
import numpy as np
import botocore
import openai
import pandas as pd
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator import Authenticate
from langchain.prompts.prompt import PromptTemplate
from botocore.client import Config
from load_environment import load_environment
from database import cleanup_candidate_data
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from botocore.exceptions import NoCredentialsError
from streamlit_extras.switch_page_button import switch_page
from pages.settings import (
    page_config,
    custom_css,
) 

page_config()
custom_css()

# Admin usernames and hashed passwords
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

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

def show_recruiter_page():
    st.subheader("Recruiter Section", divider="blue")
    expander = st.expander(":information_source:  :blue[**About**]")
    expander.info("""
        Talent-GPT is a powerful tool designed to assist recruiters and HR professionals in the hiring process. It combines the capabilities of a chatbot and data analysis to help you make informed decisions when selecting candidates for job positions. Here's a brief overview of what Talent-GPT can do:

        - **ChatBot**: Talent-GPT provides a chatbot interface that allows you to interact with it using natural language. You can ask questions about candidates, job requirements, or any other relevant topics, and the chatbot will provide SQL queries to retrieve the requested information from the database.

        - **Dashboard**: The dashboard provides you with visual insights into the candidate data. You can view statistics on candidate locations, years of experience, certifications, skills, education degrees, and more. These insights can help you identify trends and make data-driven decisions.

        - **Candidate Management**: Talent-GPT allows you to manage candidate data efficiently. You can view and select candidates, download their resumes, and even delete selected candidates if needed.

        - **Data Analysis**: The app offers data analysis features like generating charts and visualizations based on the candidate data. This helps you gain a better understanding of your candidate pool.

        Talent-GPT is designed to save you time and improve your hiring process by providing quick and accurate SQL queries, data visualizations, and candidate management tools. Give it a try and enhance your recruitment experience!

        If you have any questions or need assistance, feel free to use the chatbot or explore the dashboard for insights.

    """)
    name, authentication_status, username = authenticator.login('Login', 'main')

    if st.session_state["authentication_status"] == False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] == None:
        st.warning('Please enter your username and password')
    elif st.session_state["authentication_status"]:
        authenticator.logout('Logout', 'main')
        # st.subheader(f'Welcome :orange[_{st.session_state["name"]}_]',anchor=False)

        if st.button(":left_speech_bubble:",type="primary"):
            switch_page("chat")

        tab1, tab2 = st.tabs([
            "**Generate Insights** ",
            "**Dashboard**"]
            )

        with tab1:
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
            gd.configure_selection(selection_mode='multiple',use_checkbox=True)
            gd.configure_pagination(enabled=True, paginationAutoPageSize=True)
            gd.configure_side_bar()
            gridoptions = gd.build()
            table = AgGrid(df, gridOptions=gridoptions,
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
          
            selected_rows = table["selected_rows"]
            print(selected_rows)

            if selected_rows:
                # Extract the Candidate ID values from the selected rows and store them in the variable
                selected_candidate_ids = [row['Candidate ID'] for row in selected_rows]
                selected_candidate_name = [row['Name'] for row in selected_rows]

                delete_button = st.button("Delete Selected Candidates", key="delete_button", type="primary")
                if delete_button:
                    deleted_candidates = []
                    for candidate_id, candidate_name in zip(selected_candidate_ids, selected_candidate_name):
                        old_folder = "cr-resumegpt"
                        new_folder = "resumes_deleted"
                        for resume in selected_rows:
                            candidate_id = resume["Candidate ID"]
                            candidatename = resume["Name"]
                            old_key = f"{old_folder}/{candidate_id}_{candidatename}.pdf"
                            new_key = f"{new_folder}/{candidate_id}_{candidatename}.pdf"
                            try:
                                s3.copy_object(Bucket='cr-resumegpt', CopySource={'Bucket': 'cr-resumegpt', 'Key': old_key}, Key=new_key)
                                s3.delete_object(Bucket='cr-resumegpt', Key=old_key)
                            except NoCredentialsError:
                                st.error("AWS credentials not available. Please check your credentials configuration.")
                                break
                        cleanup_candidate_data(candidate_id)
                        deleted_candidates.append(candidate_name)

                    if deleted_candidates:
                        st.markdown('Deleted Candidates are: **{}**'.format(deleted_candidates))

        with tab2:
            cursor = connection.cursor()
            st.markdown('''
                # Dashboard '''
            )
            col3, col4 = st.columns((1,1))
            with col3:
                cursor.execute(''' SELECT Location, COUNT(*) as CandidateCount
                FROM PersonalInformation
                GROUP BY Location
                ORDER BY CandidateCount DESC
                LIMIT 5;
                ''')
                location_data = cursor.fetchall()
                print(location_data)
                wdf = pd.DataFrame(location_data, columns=['Location', 'CandidateCount'])
                wdf = wdf[wdf['Location'] != '']
                st.markdown('''### Top 5 Locations''')
                # Create a bar chart using Streamlit
                st.bar_chart(wdf.set_index('Location'))

            with col4:
                cursor.execute('''
                    SELECT
                        CASE
                            WHEN COALESCE(OverallYearsOfExperience, 0) = 0 THEN 0
                            ELSE COALESCE(OverallYearsOfExperience, 0)
                        END as ExperienceInYears,
                        COUNT(*) as Count
                    FROM ExperienceDetails
                    GROUP BY CASE
                        WHEN COALESCE(OverallYearsOfExperience, 0) = 0 THEN 0
                        ELSE COALESCE(OverallYearsOfExperience, 0)
                    END;
                ''')
                experience_data = cursor.fetchall()
                edf = pd.DataFrame(experience_data, columns=['ExperienceInYears', 'Count'])
                st.markdown('### Experience in Years')
                fig, ax = plt.subplots()
                ax.pie(edf['Count'], labels=edf['ExperienceInYears'], autopct='%1.1f%%', startangle=90)
                ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.
                # Save the pie chart as an image
                image = fig.savefig('pie_chart.png', format='png')
                # Display the saved image using Streamlit
                st.image('pie_chart.png')

            col5, col6 = st.columns((1,1))
            with col5:
                cursor.execute(''' SELECT COALESCE(w.ExperienceInYears, 0) as ExperienceInYears, COUNT(c.CandidateID) as CertificationCount 
                                FROM cr.PersonalInformation p LEFT JOIN  cr.WorkExperiences w 
                                ON p.CandidateID = w.CandidateID LEFT JOIN cr.Certification c 
                                ON p.CandidateID = c.CandidateID 
                                GROUP BY p.CandidateID, COALESCE(w.ExperienceInYears, 0); 
                ''')
                certificate_experience_data = cursor.fetchall()
                cdf = pd.DataFrame(certificate_experience_data, columns=['ExperienceInYears', 'CertificationCount'])
                x_data = cdf['ExperienceInYears']
                y_data = cdf['CertificationCount']
                # Create a scatter plot
                plt.figure(figsize=(8, 6))
                plt.scatter(x_data, y_data, alpha=0.5)
                plt.xlabel('Experience in Years')
                plt.ylabel('Certification Count')
                st.markdown('### Certification over Experience')
                st.pyplot(plt)

            with col6:
                cursor.execute('''
                SELECT
                    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(TechnicalSkill, ',', numbers.n), ',', -1)) AS skill,
                    AVG(E.OverallYearsofExperience) AS AverageExperience,
                    COUNT(*) AS NumberOfCandidates
                FROM
                    cr.ExperienceDetails E
                JOIN
                    cr.PersonalInformation P ON E.CandidateID = P.CandidateID
                JOIN
                    (
                        SELECT
                            1 + units.i + tens.i * 10 AS n
                        FROM
                            (SELECT 0 i UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) units
                        CROSS JOIN
                            (SELECT 0 i UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
                    ) AS numbers
                WHERE
                    numbers.n <= 1 + LENGTH(TechnicalSkill) - LENGTH(REPLACE(TechnicalSkill, ',', ''))
                GROUP BY
                    skill
                ORDER BY
                    NumberOfCandidates DESC
                LIMIT 10;
                ''')

                columns = [desc[0] for desc in cursor.description]  # Get column names
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]  # Convert to list of dictionaries

                # Extract data for the bubble chart
                skills = [result['skill'] for result in results]
                average_experience = [result['AverageExperience'] for result in results]
                num_candidates = [result['NumberOfCandidates'] for result in results]

                # Define a scaling factor for bubble size
                scaling_factor = 200  # You can adjust this as needed

                # Normalize the data for the heatmap color
                min_value = min(num_candidates)
                max_value = max(num_candidates)
                normalized_values = [(value - min_value) / (max_value - min_value) for value in num_candidates]

                # Create the bubble chart with a heatmap color scheme
                plt.figure(figsize=(8, 6))
                sc = plt.scatter(num_candidates, average_experience, s=scaling_factor * np.array(num_candidates), c=normalized_values, cmap='coolwarm', alpha=0.7)

                # Add labels for each bubble
                for i, skill in enumerate(skills):
                    plt.annotate(skill, (num_candidates[i], average_experience[i]), fontsize=10, ha='center')

                # Add a colorbar for the heatmap
                cbar = plt.colorbar(sc)
                cbar.set_label('Heatmap Intensity')

                plt.xlabel('Number of Candidates')
                plt.ylabel('Average Experience')
                st.markdown('### Top 10 Skills')
                st.pyplot(plt) 

            col7, col8 = st.columns((1,1))
            
            with col7:
                # SQL query to fetch Skill data
                cursor.execute('''SELECT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(TechnicalSkill, ', ', n), ', ', -1)) AS TechnicalSkill, COUNT(*) AS SkillCount
                FROM ExperienceDetails JOIN (
                SELECT 1 AS n UNION ALL
                SELECT 2 UNION ALL
                SELECT 3 UNION ALL
                SELECT 4
                ) AS numbers ON CHAR_LENGTH(TechnicalSkill)
                -CHAR_LENGTH(REPLACE(TechnicalSkill, ', ', '')) >= n - 1
                GROUP BY TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(TechnicalSkill, ', ', n), ', ', -1))
                ORDER BY SkillCount DESC
                LIMIT 10;''')
                skill_experience_data = cursor.fetchall()
                sdf = pd.DataFrame(skill_experience_data, columns=['TechnicalSkill', 'SkillCount'])
                sdf = sdf[sdf['TechnicalSkill'] != '']
                st.markdown('''### Individual Technical Skill Counts''')
                # Create a bar chart using Streamlit
                st.bar_chart(sdf.set_index('TechnicalSkill'))

            with col8:
                # SQL query to fetch work experience data
                cursor.execute('''select Degree,count(*) as DegreeCount from cr.EducationalDetails group by Degree order by DegreeCount Desc LIMIT 10;''')
                work_experience_data = cursor.fetchall()
                wdf = pd.DataFrame(work_experience_data, columns=['Degree', 'DegreeCount'])
                wdf = wdf[wdf['Degree'] != '']
                st.markdown('''### Education Degrees and Counts''')
                # Create a bar chart using Streamlit
                st.bar_chart(wdf.set_index('Degree')) 
show_recruiter_page()