# **Use Case: Resume Parser for Extracting User Information**

### **Business Problem**:
Hiring processes involve sorting through numerous resumes to identify the most suitable candidates, a time-consuming and error-prone task. Manually analyzing resumes can result in overlooking important qualifications and skills. Organizations require an efficient solution to automate and enhance the resume analysis process while extracting valuable insights from the data.

### **Solution**:
The use of a resume parser, employing technologies like PyResparser and PDFMiner, offers a transformative solution to this challenge. PyResparser is utilized to extract user information from resumes, while PDFMiner aids in converting resume PDFs into text format, facilitating further analysis.

### **Potential Users:**
**Human Resources Teams**: HR departments of companies can use the resume parser to streamline and expedite the resume screening process, ensuring the identification of the most qualified candidates.
**Recruitment Agencies**: Recruitment agencies can use the technology to efficiently match candidates with job opportunities, enhancing their service quality.
**Job Boards and Career Websites**: Platforms hosting job listings can incorporate resume parsing to help candidates submit their information more conveniently and accurately.

### **Potential Impact:**
**Time and Resource Saving**s: Resume parsing reduces the time and resources required for manual screening, allowing recruiters to focus on higher-value tasks.
**Enhanced Efficiency**: Automation ensures thorough analysis of numerous resumes simultaneously, reducing the chances of overlooking crucial qualifications.
**Improved Candidate Matching**: Accurate extraction of skills and qualifications enhances the matching process, leading to the identification of better-fit candidates.
**Reduced Bias**: The use of technology minimizes human bias in screening, leading to a fair assessment of candidates based on their qualifications.
**Strategic Insights**: Analyzing trends in skills and experiences provides insights into the job market, helping organizations refine their hiring strategies.

### **Data:**
The data primarily consists of resume documents in PDF format. The extracted text serves as the input for analysis. The data may include personal information, contact details, work experience, education history, skills, and more.

### **Approach:**
**PDF to Text Conversion**: PDFMiner is employed to convert resume PDFs into text format, making the data accessible for further analysis.
**Information Extraction**: PyResparser is used to extract user information, such as name, contact details, work experience, education, and skills, from the parsed text.
**Data Storage and Analysis**: The extracted information is stored in a structured format, allowing for easy querying and analysis.


### **High Level Diagram:**
![HLD](https://github.com/mohtasham9/Resume-parser-nlp/assets/77109645/1569129a-15ee-4c43-8d3b-735d1cad8c74)

- Resumes are uploaded to the application.
- Using **pdfMiner** to convert the pdf to text. Then with the help of the **PyResparser** NLP library, we are extracting the information. Such as Name, Email_id, Contact No., and Skill Set.
- Then we store the data in the **SQL** database. 
- We user passes a query to the application it gets embedded and then passed to the LLM to generate a SQL query.
- Generated SQL query then is used to fetch the data from the SQL and with the query it is passed on to the LLM to generate a response to the user query. 


### **Demo**
In the application, we have two user modes: Normal User and Admin Section. 
Below is the Demo of the **Normal User** Section. 
- In the Normal user section user will upload the Resume from the local drive using the choose your resume option. By dragging or using the browse file option. 
- Once the user has uploaded the resume the application will use NLP techniques to extract the basic personal information and the skill set of the user.
- User can view the uploaded resume and the extracted information such as Name, Contact No., Email id, No. of Resume Page, and Skills.
- All the relevant information is then stored in the SQL Database.
    
![Normal_User](https://github.com/mohtasham9/Resume-parser-nlp/assets/77109645/12c10150-6141-4563-9b51-27dde4228617)

Below is the Demo of the **Admin User** Section.
- The user will be prompted to enter the admin username and password.
- Once the user is validated user can view all the resumes uploaded into the application with date and time. 
- It will also show each resume's extracted information in a tabular format. 

![Untitled (2)](https://github.com/mohtasham9/Resume-parser-nlp/assets/77109645/f6691321-0643-4818-9ef4-9446b8c3b9ba)

### **Run Application**

To use this application, you must create an API Key with Open AI and pass it as an env variable. The steps are mentioned below:

1. Create a file named '.env' in the project root directory
2. Paste the following list of key-value pairs as mentioned below and save the file.

       OPENAI_API_KEY = "replace-with-your-open-ai-ai-key"
    
3. In your terminal, create a virtual environment and install requirements from the requirements file by running following command.

   `python -m pip install -r requirements.txt --no-cache`
4. Run following command from the project root directory to launch the streamlit application.

   `streamlit run main.py`
5. Browse `http://<IP_ADDRESS>:8501/` to see the application.
6. Optionally, you can build a docker image and deploy as a container after step 2.
7. To build, docker image, execute following in the project root directory.

    `docker build -t resume_parser:Dockerfile .`
8. To run, the container, execute the command: `docker run -d -p 80:8501 resume_parser:Dockerfile`

### **Conclusion**:
The use of resume parsing technology powered by PyResparser and PDFMiner presents a transformative solution to the time-consuming and error-prone process of manual resume screening. By automating the extraction of user information and converting PDFs into text format, organizations can significantly enhance their hiring processes, leading to better candidate matching, reduced bias, and strategic insights into the job market. This technology empowers HR teams, recruitment agencies, and job platforms to streamline their operations and make more informed decisions.
