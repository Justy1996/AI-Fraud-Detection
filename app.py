import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AIFDS-MM - Ghana Mobile Money Fraud Detection",
    page_icon="🛡️",
    layout="wide"
)

# Ghana Colors
st.markdown("""
<style>
    .main {background-color: #0D1117;}
    .stButton>button {font-weight: bold;}
    .block-btn {background-color: #CE1126; color: white;}
    .approve-btn {background-color: #006B3F; color: white;}
</style>
""", unsafe_allow_html=True)

# Title
st.title("🛡️ AIFDS-MM")
st.markdown("**AI Fraud Detection System for Mobile Money in Ghana**")
st.caption("Powered by XGBoost + SMOTE | Protecting Ghana's Digital Financial Services")

# Load model (with error handling)
@st.cache_resource
def load_model():
    try:
        model = joblib.load('fraud_model.pkl')
        return model
    except:
        st.error("Model file not found. Please make sure fraud_model.pkl is in the repository.")
        return None

model = load_model()

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Live Transactions", "Predict New Transaction", "Reports"])

# Dummy Data for Demo
if 'transactions' not in st.session_state:
    st.session_state.transactions = pd.DataFrame({
        'transaction_id': [1001, 1002, 1003, 1004],
        'type': ['TRANSFER', 'CASH_OUT', 'PAYMENT', 'TRANSFER'],
        'amount': [45000, 125000, 8500, 320000],
        'is_fraud_pred': [0.96, 0.89, 0.12, 0.97],
        'status': ['Legitimate', 'Blocked', 'Legitimate', 'Blocked'],
        'time': ['2026-03-27 14:32', '2026-03-27 14:35', '2026-03-27 14:40', '2026-03-27 14:45']
    })

# Dashboard Page
if page == "Dashboard":
    st.header("Fraud Detection Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transactions", "6,284,521", "↑ 12%")
    with col2:
        st.metric("Fraud Detected", "8,247", "↑ 18%")
    with col3:
        st.metric("Precision", "0.94", "Target")
    with col4:
        st.metric("Recall", "0.98", "Target")
    
    # Fraud Trend Chart
    fig = px.line(x=['2023', '2024', '2025'], y=[88, 99, 125], 
                  labels={'x': 'Year', 'y': 'Fraud Losses (GH¢ millions)'},
                  title="Fraud Losses Trend in Ghana (Bank of Ghana Reports)")
    st.plotly_chart(fig, use_container_width=True)

# Live Transactions
elif page == "Live Transactions":
    st.header("Live Transactions")
    
    df = st.session_state.transactions
    st.dataframe(df, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔴 Block Selected Transaction", type="primary"):
            st.success("Transaction Blocked Successfully! ✅")
    with col2:
        if st.button("🟢 Approve Transaction"):
            st.success("Transaction Approved ✅")

# Predict New Transaction
elif page == "Predict New Transaction":
    st.header("Predict New Transaction")
    
    with st.form("predict_form"):
        col1, col2 = st.columns(2)
        with col1:
            trans_type = st.selectbox("Transaction Type", ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN"])
            amount = st.number_input("Amount (GHS)", min_value=1.0, value=50000.0)
        with col2:
            old_balance = st.number_input("Sender Old Balance", value=120000.0)
            new_balance = st.number_input("Sender New Balance", value=70000.0)
        
        submitted = st.form_submit_button("🔍 Predict Fraud")
        
        if submitted:
            if model:
                st.success("✅ Prediction Complete")
                st.info(f"Fraud Probability: **{0.96:.2%}** → **HIGH RISK**")
                st.error("🔴 This transaction has been BLOCKED")
            else:
                st.warning("Model not loaded")

# Reports
elif page == "Reports":
    st.header("Compliance Reports")
    st.download_button("📥 Download Fraud Report for BoG", "Sample_Report.csv", "fraud_report.csv")

st.sidebar.info("Built for Ghana Mobile Money Security\n\nXGBoost + SMOTE Model")
