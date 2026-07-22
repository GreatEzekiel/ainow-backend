import streamlit as st
import requests

st.set_page_config(page_title="AINOW Dashboard", layout="wide")
st.title("📈 AINOW Interactive Dashboard")

# Directly load data without asking for credentials or tokens
if st.button("Load Tickers"):
    with st.spinner("Fetching data..."):
        try:
            # Simple GET request with no Authorization header
            response = requests.get("http://127.0.0.1:8000/api/v1/tickers")
            
            if response.status_code == 200:
                st.success("Data loaded successfully!")
                st.json(response.json())
            else:
                st.error(f"Backend returned error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Could not connect to FastAPI server: {e}")