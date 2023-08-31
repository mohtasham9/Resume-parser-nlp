# Use the official Python image
FROM python:3.7

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file first to leverage Docker cache
COPY requirements.txt .

# Install required Python packages
RUN pip install -r requirements.txt --default-timeout=100 future

# Copy the rest of the application files to the container's working directory
COPY . .


RUN python -m spacy download en_core_web_sm

RUN apt-get -y update && apt -get install software-properties-common \
&& add-apt-repository ppa:deadsnakes/ppa && apt install python3.10
# Expose the port that Streamlit will run on
EXPOSE 8501

# Command to run your Streamlit application
CMD ["streamlit", "run", "main.py"]
