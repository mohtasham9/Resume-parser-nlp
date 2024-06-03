import streamlit as st
import base64
from PIL import Image

def page_config():
    img = Image.open('assets/logo.png')
    st.set_page_config(
        page_title="Talent-GPT",
        layout="wide",
        initial_sidebar_state="collapsed",
        page_icon=img,
    )

@st.cache_resource
def custom_css():
    st.markdown("""
        <style>
            #MainMenu, header, footer {visibility: hidden;}
        </style>
        """,unsafe_allow_html=True)

    header_style = """
    <style>
        .stApp {
            margin-top: -20px;
        }
    </style>
    """
    st.markdown(header_style, unsafe_allow_html=True)

    st.markdown(
        """
    <style>
        [data-testid="collapsedControl"] {
            display: none
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2) 
    with open("assets/Title-Image.png", "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    col1.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin-top: -3rem;">
            <h1 style="color: #001c8b;"> Talent-GPT <h1>
        </div>
        """,
        unsafe_allow_html=True
        )
    col2.markdown(
        f"""
        <div style="display: flex; justify-content: flex-end; margin-top: -4rem;">
            <img style="width: 10rem;" src="data:image/png;base64,{data}" >
        </div>
        """,
        unsafe_allow_html=True
    )