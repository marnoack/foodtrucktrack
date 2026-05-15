import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Business Drive Portal",
    page_icon="📂",
    layout="wide"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: 600; border: 1px solid #e2e8f0; transition: all 0.2s; }
    .stButton>button:hover { background-color: #3b82f6; color: white; border-color: #3b82f6; transform: translateY(-1px); }
    .file-card {
        background-color: white;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 0.75rem;
    }
    .file-title { font-size: 1.05rem; font-weight: 600; color: #1e293b; text-decoration: none; }
    .file-title:hover { color: #3b82f6; }
    .metadata { color: #64748b; font-size: 0.85rem; margin-top: 4px; }
    .status-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        background-color: #f1f5f9;
        color: #475569;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 8px;
    }
    .cred-banner {
        padding: 1rem;
        border-radius: 8px;
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Google Drive Logic ---
def get_drive_service():
    """
    Initializes Google Drive service using credentials from Streamlit Secrets.
    Expected secret structure: [service_account]
    """
    try:
        # Check for the standardized service_account key in st.secrets
        if "service_account" in st.secrets:
            creds_info = dict(st.secrets["service_account"])
            scopes = ['https://www.googleapis.com/auth/drive.readonly']
            creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
            return build('drive', 'v3', credentials=creds)
        return None
    except Exception as e:
        st.error(f"Authentication Error: {str(e)}")
        return None

def search_drive_files(query_text):
    service = get_drive_service()
    if not service:
        return None # Signal that we are in demo mode/unauthenticated

    try:
        # Search for files containing the query text
        clean_query = query_text.replace("'", "\\'")
        drive_query = f"name contains '{clean_query}' and trashed = false"
        
        results = service.files().list(
            q=drive_query,
            pageSize=15,
            fields="files(id, name, mimeType, webViewLink, modifiedTime, iconLink)"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        st.error(f"Drive API Error: {str(e)}")
        return []

# --- App State ---
if 'view' not in st.session_state:
    st.session_state.view = 'dashboard'

# --- Sidebar ---
with st.sidebar:
    st.title("Business Hub")
    st.caption("Central Management System")
    st.markdown("---")
    
    if st.button("📊 Compliance Dashboard"):
        st.session_state.view = 'dashboard'
    
    if st.button("🔍 Client File Search"):
        st.session_state.view = 'search'
    
    if st.button("🔑 API Configuration"):
        st.session_state.view = 'config'
        
    st.markdown("---")
    auth_status = "✅ Connected" if "service_account" in st.secrets else "⚠️ Setup Required"
    st.write(f"**Drive Status:** {auth_status}")

# --- Views ---

if st.session_state.view == 'dashboard':
    st.title("Austin Food Truck Compliance")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Permits", "12")
    col2.metric("Upcoming Renewals", "3", delta="-1")
    col3.metric("System Health", "100%")

    st.subheader("Required Documentation")
    data = [
        {"Permit": "Mobile Food Vendor License", "Agency": "Austin Public Health", "Expiry": "2024-12-01"},
        {"Permit": "Fire Safety Certificate", "Agency": "Austin Fire Dept", "Expiry": "2024-08-15"},
        {"Permit": "Sales Tax ID", "Agency": "Texas Comptroller", "Expiry": "Permanent"},
        {"Permit": "Commissary Agreement", "Agency": "Private Commercial Kitchen", "Expiry": "2025-01-10"}
    ]
    st.dataframe(pd.DataFrame(data), use_container_width=True)

elif st.session_state.view == 'search':
    st.title("Google Drive Search")
    
    if "service_account" not in st.secrets:
        st.markdown("""
        <div class="cred-banner">
            <strong>Action Required:</strong> Google Drive credentials are not detected. 
            Go to the <b>API Configuration</b> tab to see how to connect your account.
        </div>
        """, unsafe_allow_html=True)
    
    query = st.text_input("Enter Business or Client Name", placeholder="Acme Logistics...")
    
    if query:
        with st.spinner("Querying Google Drive..."):
            files = search_drive_files(query)
            
            if files is None:
                st.info("Demo Mode: Authenticate via Sidebar to see real files.")
                # Fake results for visual demonstration
                files = [{"name": "DEMO_Contract.pdf", "mimeType": "pdf", "modifiedTime": "2024-01-01", "webViewLink": "#", "iconLink": ""}]

            if files:
                for f in files:
                    date = f.get('modifiedTime', 'Unknown').split('T')[0]
                    st.markdown(f"""
                        <div class="file-card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <a href="{f.get('webViewLink')}" target="_blank" class="file-title">{f.get('name')}</a>
                                    <div class="metadata">
                                        <span class="status-badge">{f.get('mimeType', '').split('.')[-1]}</span>
                                        Modified: {date}
                                    </div>
                                </div>
                                <code style="font-size: 0.7rem; color: #94a3b8;">{f.get('id')[:8]}...</code>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No files found matching that name.")

elif st.session_state.view == 'config':
    st.title("API & Credentials Setup")
    st.markdown("""
    To connect this app to your Google Drive, follow these steps:
    
    1. **Create Service Account**: Go to [Google Cloud Console](https://console.cloud.google.com/), create a service account, and download the **JSON Key**.
    2. **Share Folder**: Open your Google Drive folder and share it with the `client_email` found in your JSON file.
    3. **Add to Secrets**: Copy the entire content of the JSON file.
    4. **Streamlit Setup**: In your Streamlit Cloud Dashboard, go to **Settings > Secrets** and paste it exactly like this:
    """)
    
    st.code("""
[service_account]
type = "service_account"
project_id = "your-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\\n..."
client_email = "..."
...
    """, language="toml")
    
    st.success("Once you save those secrets, the 'Client File Search' will pull live data automatically.")
