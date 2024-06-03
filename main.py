import streamlit as st
from pages.candidate import show_candidate_page 
from pages.recruiter import show_recruiter_page
from pages.chat import show_chat_page
from pages.settings import (
    page_config,
    custom_css,
) 

page_config()
custom_css()

def main():
    session_state = st.session_state

    if "url" not in session_state:
        session_state.url = None

    url = st.experimental_get_query_params()

    if url:
        session_state.url = url
    else:
        url = session_state.url

    if url and url.get("path"):
        path = url["path"]
        if path == "/candidate":
            show_candidate_page()
        elif path == "/recruiter":
            show_recruiter_page()
            
show_chat_page()    
