##################################################################################
###                                                                            ###
###                 JSON Schema for CV details extraction                      ###
###                                                                            ###
##################################################################################

"""This file defines the json schema output for the CV details extraction"""

response_schema = {
    "type": "object",
    "properties": {
        "Personal_Information": {
            "type": "object",
            "properties": {
                "Name": {
                    "type": "string",
                    "description": "Name of the candidate"
                },
                "Contact_Number": {
                    "type": "string",
                    "description": "Contact number"
                },
                "Email_ID": {
                    "type": "string",
                    "description": "Email ID"
                },
                "Location": {
                    "type": "string",
                    "description": "Location details if mentioned else NA. You can mention current job location. Mention the city name only like Delhi, SanFransisco, London."
                },
                "Job_Title": {
                    "type": "string",
                    "description": "Title of their job like Data Analyst, Data Scientist, DevOps Engineer etc. If not mentioned, consider current job title."
                },
                "Date_of_Birth": {
                    "type": "string",
                    "description": "Date of Birth if mentioned else NA. Format must be in DD-MM-YYYY"
                },
                "Nationality": {
                    "type": "string",
                    "description": "Nationality if mentioned else NA"
                },
                "Languages_Known": {
                    "type": "array",
                    "description": "A list of Known Languages if mentioned else parse an empty list.",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "Name",
                "Contact_Number",
                "Email_ID",
                "Location",
                "Job_Title",
                "Date_of_Birth",
                "Nationality",
                "Languages_Known"
            ]
        },
        "Educational_Details": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Degree": {
                        "type": "string",
                        "description": "Degree or course completed."
                    },
                    "Branch": {
                        "type": "string",
                        "description": "Corresponding branch or stream or course detail if mentioned else NA"
                    },
                    "Completed_Year": {
                        "type": "integer",
                        "description": "Year of completion"
                    },
                    "GPA_or_Percentage": {
                        "type": "string",
                        "description": "Mention GPA or Percentage"
                    },
                    "School_or_College": {
                        "type": "string",
                        "description": "Mention school of college name if mentioned else say Not mentioned"
                    }
                },
                "required": [
                    "Degree",
                    "Branch",
                    "Completed_Year",
                    "GPA_or_Percentage",
                    "School_or_College"
                ]
            }
        },
        "Experience_Details": {
            "type": "object",
            "properties": {
                "Overall_years_of_experience": {
                    "type": "integer",
                    "description": "Their Overall experience in integer. If not mentioned, go through mentioned job experiences and calculate. Validate if number close to combined work experience years."
                },
                "Technical_Skills": {
                    "type": "array",
                    "description": "A list of aggregated technical skills mentioned in their resume under skills or technical skills or technical summary or core competencies",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "Overall_years_of_experience",
                "Technical_Skills"
            ]
        },
        "Work_Experiences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Company": {
                        "type": "string",
                        "description": "Current Organization"
                    },
                    "Role": {
                        "type": "string",
                        "description": "Mentioned project role or title"
                    },
                    "Start_time": {
                        "type": "string",
                        "description": "Month, YYYY"
                    },
                    "End_time": {
                        "type": "string",
                        "description": "Month, YYYY. If it is the current organization, mention current Month, YYYY. "
                    },
                    "Experience_in_years": {
                        "type": "integer",
                        "description": "Years of experience in this organization as an integer. Calculate End_time - Start_time."
                    },
                    "Key_Responsibilities": {
                        "type": "string",
                        "description": "A four sentence summary of responsibilities carried."
                    }
                },
                "required": [
                    "Company",
                    "Role",
                    "Start_time",
                    "End_time",
                    "Experience_in_years",
                    "Key_Responsibilities"
                ]
            }
        },
        "Certifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Certificate_Name": {
                        "type": "string",
                        "description": "Name of certificate earned"
                    },
                    "Year_of_Certification": {
                        "type": "string",
                        "description": "Month, YYYY of certificate earned"
                    },
                    "Certificate_Provider": {
                        "type": "string",
                        "description": "Provider of the certificate"
                    },
                    "Certificate_ID": {
                        "type": "string",
                        "description": "ID of the certificate"
                    },
                    "Skills_Covered": {
                        "type": "string",
                        "description": "List of key skills, technologies that are covered in certification. If not mentioned return NA."
                    }
                },
                "required": [
                    "Certificate_Name",
                    "Year_of_Certification",
                    "Certificate_Provider",
                    "Certificate_ID",
                    "Skills_Covered"
                ]
            }
        },
        "Courses_Completed": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Course_Name": {
                        "type": "string",
                        "description": "Name of the course"
                    },
                    "Year_of_Course_Completion": {
                        "type": "string",
                        "description": "Month, YYYY of the course completion"
                    },
                    "Course_Provider": {
                        "type": "string",
                        "description": "Company name of the course provider"
                    },
                    "Certificate_ID": {
                        "type": "string",
                        "description": "ID of the course completion certificate"
                    },
                    "Topics_Covered": {
                        "type": "string",
                        "description": "A list of topics or skills covered in this course. If not mentioned return NA"
                    }
                },
                "required": [
                    "Course_Name",
                    "Year_of_Course_Completion",
                    "Course_Provider",
                    "Certificate_ID",
                    "Topics_Covered"
                ]
            }
        }
    },
    "required": [
        "Personal_Information",
        "Educational_Details",
        "Experience_Details",
        "Work_Experiences",
        "Certifications",
        "Course_Completed"
    ]
}
