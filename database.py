import pymysql
from load_environment import load_environment

_, _, _, db_config = load_environment()

def check_existing_candidate(candidate_name, candidate_email):
    # Initialize the connection
    connection = pymysql.connect(**db_config)

    # Use a try-except block to handle potential errors
    try:
        # Create a cursor to execute SQL queries
        with connection.cursor() as cursor:
            # Query the database to check for an existing candidate
            query = "SELECT CandidateID FROM PersonalInformation WHERE Name = %s AND EmailID = %s"
            cursor.execute(query, (candidate_name, candidate_email))
            result = cursor.fetchone()

            if result:
                # An existing candidate was found; return their CandidateID
                return result[0]
            else:
                # No existing candidate found
                return None
    except Exception as e:
        # Handle any exceptions that may occur during the database operation
        print("Error:", e)
    finally:
        # Close the database connection
        connection.close()

def cleanup_candidate_data(existing_candidate_id):
    # Initialize the connection
    connection = pymysql.connect(**db_config)

    # Use a try-except block to handle potential errors
    try:
        # Create a cursor to execute SQL queries
        with connection.cursor() as cursor:
            # Delete records associated with the existing candidate
            delete_personal_query = "DELETE FROM cr.PersonalInformation WHERE CandidateID = %s"
            delete_educational_query = "DELETE FROM cr.EducationalDetails WHERE CandidateID = %s"
            delete_experience_query = "DELETE FROM cr.ExperienceDetails WHERE CandidateID = %s"
            delete_work_query = "DELETE FROM cr.WorkExperiences WHERE CandidateID = %s"
            delete_certification_query = "DELETE FROM cr.Certification WHERE CandidateID = %s"
            delete_courses_query = "DELETE FROM cr.CoursesCompleted WHERE CandidateID = %s"

            cursor.execute(delete_educational_query, (existing_candidate_id,))
            cursor.execute(delete_experience_query, (existing_candidate_id,))
            cursor.execute(delete_work_query, (existing_candidate_id,))
            cursor.execute(delete_certification_query, (existing_candidate_id,))
            cursor.execute(delete_courses_query, (existing_candidate_id))
            cursor.execute(delete_personal_query, (existing_candidate_id,))

        # Commit the changes to the database
        connection.commit()
    except Exception as e:
        # Handle any exceptions that may occur during the database operation
        print("Error:", e)
    finally:
        # Close the database connection
        connection.close()