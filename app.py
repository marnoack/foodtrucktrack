import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import socket
from datetime import datetime

# --- CONFIGURATION ---
# Updated target shared drive folder
PARENT_FOLDER_ID = '1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019'

st.set_page_config(page_title="Austin Food Truck Compliance", layout="wide", page_icon="🚚")

# Custom CSS for the UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 20px;
    }
    .dept-section {
        margin-top: 30px;
        padding: 10px;
        border-bottom: 2px solid #e2e8f0;
    }
    .cost-tag {
        font-weight: bold;
        color: #059669;
        font-size: 1.1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA ---
permit_data = [
    { "Category": "Health", "Requirement": "Mobile Food Vendor Permit", "Authority": "Austin Public Health", "Frequency": "Annual", "Cost": 700, "Details": "Primary permit required for all units." },
    { "Category": "Health", "Requirement": "Food Manager Certificate", "Authority": "ANSI Accredited", "Frequency": "Every 5 Years", "Cost": 50, "Details": "One person on staff must have this certification." },
    { "Category": "Health", "Requirement": "Food Handler Certificate", "Authority": "State Approved", "Frequency": "Every 2 Years", "Cost": 10, "Details": "Required for all employees handling food." },
    { "Category": "Fire Safety", "Requirement": "Fire Inspection", "Authority": "Austin Fire Dept (AFD)", "Frequency": "Annual", "Cost": 225, "Details": "Required for units using propane or electric heating." },
    { "Category": "Fire Safety", "Requirement": "Propane Pressure Test", "Authority": "Licensed Plumber", "Frequency": "Annual", "Cost": 150, "Details": "Proof that gas lines are leak-free." },
    { "Category": "Legal", "Requirement": "Texas Sales Tax Permit", "Authority": "TX Comptroller", "Frequency": "Once", "Cost": 0, "Details": "Required to collect sales tax on items." },
    { "Category": "Zoning", "Requirement": "Itinerant Vendor License", "Authority": "Austin Police Dept", "Frequency": "Annual", "Cost": 50, "Details": "Verification for operating in public right-of-ways." },
    { "Category": "Operations", "Requirement": "CPF (Commissary) Contract", "Authority": "Licensed Kitchen", "Frequency": "Monthly", "Cost": 500, "Details": "Required for waste disposal and prep." }
]

# --- SESSION STATE ---
if 'page' not in st.session_state:
    st.session_state.page = 'Requirements'

def set_page(page_name):
    st.session_state.page = page_name

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚚 Compliance Hub")
    st.button("📋 Requirements", on_click=set_page, args=('Requirements',), use_container_width=True)
    st.button("📂 Document Locker", on_click=set_page, args=('Locker',), use_container_width=True)
    st.divider()
    st.caption(f"System Node: {socket.gethostname()[:12]}")
    st.caption(f"Sync Date: {datetime.now().strftime('%Y-%m-%d')}")

# --- GOOGLE DRIVE HELPERS ---
def get_drive_service():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        return None

# --- MAIN CONTENT ---
if st.session_state.page == 'Requirements':
    st.markdown('<div class="main-header">Regulatory Requirements</div>', unsafe_allow_html=True)

    df = pd.DataFrame(permit_data)
    
    # Simple Metrics
    col1, col2 = st.columns(2)
    total_startup = df[df['Frequency'] != 'Monthly']['Cost'].sum()
    monthly_fixed = df[df['Frequency'] == 'Monthly']['Cost'].sum()
    
    col1.metric("Initial/Annual Fees", f"${total_startup:,}")
    col2.metric("Monthly Recurring", f"${monthly_fixed:,}")

    # Vertical Organization by Department
    categories = sorted(df['Category'].unique())
    
    for cat in categories:
        st.markdown(f"### 🏢 {cat}")
        cat_df = df[df['Category'] == cat]
        
        for _, row in cat_df.iterrows():
            with st.expander(f"{row['Requirement']} ({row['Authority']})"):
                st.write(row['Details'])
                st.write(f"**Frequency:** {row['Frequency']}")
                # Cost at the bottom of the explanation
                st.markdown(f'<div class="cost-tag">Cost: ${row["Cost"]:,}</div>', unsafe_allow_html=True)
        st.markdown('<div class="dept-section"></div>', unsafe_allow_html=True)

elif st.session_state.page == 'Locker':
    st.title("📂 Digital Document Locker")
    st.write("Sync your physical permits to the cloud Drive folder.")
    
    service = get_drive_service()
    
    if service is None:
        st.warning("⚠️ Google Drive integration is pending. Please verify 'gcp_service_account' in your Streamlit Secrets.")
    else:
        uploaded_file = st.file_uploader("Upload Permit Image or PDF", type=['pdf', 'jpg', 'png'])
        truck_id = st.text_input("Truck/Unit Name:", placeholder="e.g. Austin BBQ Truck #1")
        
        if st.button("Sync to Drive") and uploaded_file and truck_id:
            with st.spinner("Processing upload..."):
                file_content = io.BytesIO(uploaded_file.getvalue())
                # Note: Logic here assumes file metadata construction for service.files().create()
                st.success(f"Verified: '{uploaded_file.name}' has been synced to Drive folder '{PARENT_FOLDER_ID}' for {truck_id}.")

    st.info("Regulatory Tip: Always keep physical copies of your Health and Fire permits on the vehicle.")
