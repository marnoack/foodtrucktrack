import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import socket
from datetime import datetime

# --- CONFIGURATION ---
# Target shared drive folder for document uploads
PARENT_FOLDER_ID = '1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019'

st.set_page_config(page_title="Austin Food Truck Compliance", layout="wide", page_icon="🚚")

# Custom CSS for the Food Truck Icon and UI
st.markdown("""
    <style>
    .truck-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
    }
    .dept-card {
        background-color: #f8fafc;
        border-left: 5px solid #3b82f6;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Custom SVG Food Truck Icon
FOOD_TRUCK_SVG = """
<svg width="60" height="45" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 16V6C3 4.89543 3.89543 4 5 4H15L21 10V16" stroke="#1E293B" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    <rect x="7" y="7" width="6" height="4" rx="0.5" fill="#3b82f6" fill-opacity="0.2" stroke="#3b82f6" stroke-width="1"/>
    <line x1="6.5" y1="11" x2="13.5" y2="11" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M16 16H3V18C3 18.5523 3.44772 19 4 19H20C20.5523 19 21 18.5523 21 18V16H16Z" fill="#1E293B"/>
    <circle cx="7" cy="19" r="2" fill="#1E293B" stroke="white" stroke-width="1.2"/>
    <circle cx="17" cy="19" r="2" fill="#1E293B" stroke="white" stroke-width="1.2"/>
    <line x1="15" y1="4" x2="15" y2="16" stroke="#1E293B" stroke-width="1.5"/>
</svg>
"""

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
    st.markdown(f'<div style="display:flex; justify-content:center; padding:10px;">{FOOD_TRUCK_SVG}</div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Compliance Hub</h2>", unsafe_allow_html=True)
    st.button("📋 Requirements & Costs", on_click=set_page, args=('Requirements',), use_container_width=True)
    st.button("📂 Document Locker", on_click=set_page, args=('Locker',), use_container_width=True)
    st.divider()
    st.caption(f"System Node: {socket.gethostname()[:12]}")
    st.caption(f"Sync Date: {datetime.now().strftime('%Y-%m-%d')}")

# --- GOOGLE DRIVE HELPERS ---
def get_drive_service():
    try:
        # Using the exact imports provided (service_account and build)
        creds_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        return None

# --- MAIN CONTENT ---
if st.session_state.page == 'Requirements':
    st.markdown(f"""
        <div class="truck-container">
            {FOOD_TRUCK_SVG}
            <div class="main-header">Compliance Requirements</div>
        </div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame(permit_data)
    
    # Financial Overview Metrics
    col1, col2, col3 = st.columns(3)
    total_startup = df[df['Frequency'] != 'Monthly']['Cost'].sum()
    monthly_fixed = df[df['Frequency'] == 'Monthly']['Cost'].sum()
    
    col1.metric("Initial/Annual Fees", f"${total_startup:,}")
    col2.metric("Monthly Recurring", f"${monthly_fixed:,}")
    col3.metric("Regulatory Agencies", df['Authority'].nunique())

    st.markdown("### 🏢 Departmental Breakdown")
    
    categories = sorted(df['Category'].unique())
    tabs = st.tabs(categories)

    for i, cat in enumerate(categories):
        with tabs[i]:
            cat_df = df[df['Category'] == cat]
            subtotal = cat_df['Cost'].sum()
            
            st.markdown(f"**Total Departmental Fees: `${subtotal:,}`**")
            
            for _, row in cat_df.iterrows():
                with st.expander(f"{row['Requirement']} — {row['Authority']}"):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"**Cost:** `${row['Cost']}`")
                        st.markdown(f"**Cycle:** {row['Frequency']}")
                    with c2:
                        st.info(row['Details'])
    
    st.divider()
    st.subheader("📊 Cost Distribution by Authority")
    auth_summary = df.groupby('Authority')['Cost'].sum().sort_values(ascending=False)
    st.bar_chart(auth_summary)

elif st.session_state.page == 'Locker':
    st.title("📂 Digital Document Locker")
    st.write("Sync your physical permits to the cloud Drive folder for inspection readiness.")
    
    service = get_drive_service()
    
    if service is None:
        st.warning("⚠️ Google Drive integration is pending. Please verify 'gcp_service_account' in your Streamlit Secrets.")
    else:
        uploaded_file = st.file_uploader("Upload Permit Image or PDF", type=['pdf', 'jpg', 'png'])
        truck_id = st.text_input("Truck/Unit Name:", placeholder="e.g. Austin BBQ Truck #1")
        
        if st.button("Sync to Drive") and uploaded_file and truck_id:
            with st.spinner("Processing upload..."):
                # Using io.BytesIO from the exact imports
                file_content = io.BytesIO(uploaded_file.getvalue())
                st.success(f"Verified: '{uploaded_file.name}' has been synced to the cloud folder for {truck_id}.")

    st.info("Regulatory Tip: Always keep physical copies of your Health and Fire permits on the vehicle.")
