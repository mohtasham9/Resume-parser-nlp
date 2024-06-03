import os
import openai
from dotenv import load_dotenv, find_dotenv

def load_environment():
    """
    Load environment variables and database configuration.
    """
    _ = load_dotenv(find_dotenv())
    openai.api_key = os.environ["OPENAI_API_KEY"]
    aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
    aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]

    db_config = {
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],  # Enter your database password here
        "host": os.environ["DB_HOST"],
        "database": os.environ["DB_DATABASE"],  # Name of the database
    }
    return openai.api_key, aws_access_key_id, aws_secret_access_key, db_config