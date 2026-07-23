import streamlit as st
import requests
import pandas as pd

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(page_title="AINOW Analytics Dashboard", layout="wide")
st.title("📈 AINOW Interactive Financial Dashboard")

# Initialize Session State Variables
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None

# --- Sidebar Authentication Panel ---
st.sidebar.header("🔑 Authentication")

if not st.session_state.token:
    auth_mode = st.sidebar.radio("Mode", ["Login", "Register"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if auth_mode == "Register":
        email = st.sidebar.text_input("Email")
        if st.sidebar.button("Sign Up"):
            res = requests.post(f"{API_BASE_URL}/auth/register", json={"username": username, "email": email, "password": password})
            if res.status_code == 201:
                st.sidebar.success("Account created! You can now log in.")
            else:
                st.sidebar.error(res.json().get("detail", "Registration failed"))

    elif auth_mode == "Login":
        if st.sidebar.button("Log In"):
            res = requests.post(f"{API_BASE_URL}/auth/token", data={"username": username, "password": password})
            if res.status_code == 200:
                st.session_state.token = res.json()["access_token"]
                st.session_state.username = username
                st.sidebar.success(f"Logged in as {username}")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")
else:
    st.sidebar.success(f"Logged in as **{st.session_state.username}**")
    if st.sidebar.button("Log Out"):
        st.session_state.token = None
        st.session_state.username = None
        st.rerun()

# --- Main Dashboard Content ---
headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

st.subheader("📊 System Status")
try:
    metrics_res = requests.get(f"{API_BASE_URL}/metrics")
    if metrics_res.status_code == 200:
        m_data = metrics_res.json()
        col1, col2, col3 = st.columns(3)
        col1.metric("Status", m_data.get("status", "Offline").upper())
        col2.metric("Total Price Records", m_data.get("total_records", 0))
        col3.metric("Active Tickers", m_data.get("active_tickers", 0))
    else:
        st.warning("Could not load backend metrics.")
except Exception as e:
    st.error(f"Backend Server Connection Error: {e}")

st.markdown("---")

if st.session_state.token:
    st.subheader("📈 Ticker Market Summary")
    if st.button("Refresh Tickers"):
        with st.spinner("Fetching authenticated market data..."):
            res = requests.get(f"{API_BASE_URL}/tickers", headers=headers)
            if res.status_code == 200:
                tickers_df = pd.DataFrame(res.json())
                st.dataframe(tickers_df, use_container_width=True)
            else:
                st.error(f"Error {res.status_code}: {res.text}")

    st.subheader("📉 Ticker Price History")
    selected_ticker = st.text_input("Enter Ticker Symbol (e.g., NGXBNK)", value="NGXBNK")
    if st.button("Load Chart Data"):
        res = requests.get(f"{API_BASE_URL}/chart/{selected_ticker.upper()}", headers=headers)
        if res.status_code == 200:
            chart_df = pd.DataFrame(res.json())
            chart_df["date"] = pd.to_datetime(chart_df["date"])
            st.line_chart(chart_df.set_index("date")[["close_price", "sma_10", "sma_20"]])
        else:
            st.error(f"Error {res.status_code}: {res.text}")
else:
    st.info("👈 Please log in via the sidebar to access protected stock data and prediction metrics.")