# Import the required libraries
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
import os  # Import the os library

def create_embeddings(api):
    # Check if the faiss_index already exists
    if os.path.exists("faiss_index"):
        print("faiss_index already exists. Skipping creation.")
    else:
        # load the ddl file
        loader = TextLoader('db.sql')
        data = loader.load()

        # split the text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
        texts = text_splitter.split_documents(data)

        # Create embeddings from the doc using the provided API key
        embeddings = OpenAIEmbeddings(openai_api_key=api)
        docsearch = FAISS.from_documents(texts, embeddings)

        # save the faiss index
        docsearch.save_local("faiss_index")
        print("faiss_index created successfully.")
