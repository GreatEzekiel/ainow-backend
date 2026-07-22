import streamlit as st
import requests

st.set_page_config(page_title="AINOW Dashboard", layout="wide")
st.title("📈 AINOW Interactive Dashboard")

# Add a text input for JWT Token if authentication is required
token = st.text_input("Bearer Token (Optional)", type="password")

if st.button("Load Tickers"):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    with st.spinner("Fetching data..."):
        response = requests.get("http://127.0.0.1:8000/api/v1/tickers", headers=headers)
        
        if response.status_code == 200:
            st.success("Data fetched successfully!")
            st.json(response.json())
        else:
            st.error(f"Error {response.status_code}: {response.text}")