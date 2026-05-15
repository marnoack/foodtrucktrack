import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Business Drive Portal",
    page_icon="📂",
    layout="wide"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: 600; transition: 0.3s; }
    .stButton>button:hover { background-color: #4285F4; color: white; border-color: #4285F4; }
    .file-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #4285F4;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    .file-card:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
    .file-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a73e8;
        text-decoration: none;
    }
    .file-title:hover { text-decoration: underline; }
    .metadata {
        color: #5f6368;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .status-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        background-color: #e8f0fe;
        color: #1967d2;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Google Drive Service Initialization ---
def get_drive_service():
    """
    Initializes the Google Drive API service using a service account.
    Requires 'google_auth' dictionary in st.secrets.
    """
    try:
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        
        # Check for credentials in Streamlit Secrets
        if "google_auth" not in st.secrets:
            st.warning("Google Drive credentials not found in st.secrets. Using demonstration mode.")
            return None
            
        creds_info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(
            creds_info, 
            scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Failed to initialize Drive API: {str(e)}")
        return None

def search_drive_files(query_text):
    """
    Searches for files in Google Drive shared with the service account.
    """
    service = get_drive_service()
    if not service:
        # Static demo data returned if API is not configured
        return [
            {
                "name": f"Archive_{query_text}_2024.pdf",
                "mimeType": "application/pdf",
                "webViewLink": "#",
                "modifiedTime": "2024-05-15T12:00:00Z",
                "iconLink": "https://fonts.gstatic.com/s/i/productlogos/drive/v2/web-24.png"
            }
        ]

    # Sanitize and prepare query
    clean_query = query_text.replace("'", "\\'")
    drive_query = f"name contains '{clean_query}' and trashed = false"
    
    try:
        results = service.files().list(
            q=drive_query,
            pageSize=20,
            fields="files(id, name, mimeType, webViewLink, modifiedTime, iconLink)"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        st.error(f"Error querying Google Drive: {str(e)}")
        return []

# --- Navigation State Management ---
if 'view' not in st.session_state:
    st.session_state.view = 'dashboard'

# --- Sidebar ---
with st.sidebar:
    st.title("📂 Business Hub")
    st.markdown("---")
    
    if st.button("📊 Compliance Dashboard"):
        st.session_state.view = 'dashboard'
    
    if st.button("🔍 Client File Search"):
        st.session_state.view = 'search'
        
    st.markdown("---")
    if "google_auth" in st.secrets:
        st.success("Google API: Active")
    else:
        st.info("Status: Demo Mode")
    st.caption("v2.1 | Austin, TX")

# --- View: Dashboard (Austin Permit Tracker) ---
if st.session_state.view == 'dashboard':
    st.title("Austin Food Truck Compliance")
    
    # Key Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Permits", "8", "City of Austin")
    col2.metric("Total Est. Cost", "$1,785", "Initial Setup")
    col3.metric("Renewal Cycle", "Annual", "Fire/Health")

    st.markdown("### 📋 Essential Permits & Licenses")
    
    permit_data = [
        {"Category": "Health", "Requirement": "Mobile Food Vendor Permit", "Authority": "Austin Public Health", "Cost": "$700"},
        {"Category": "Fire Safety", "Requirement": "Fire Inspection", "Authority": "Austin Fire Dept", "Cost": "$225"},
        {"Category": "Legal", "Requirement": "Texas Sales Tax Permit", "Authority": "TX Comptroller", "Cost": "Free"},
        {"Category": "Operations", "Requirement": "CPF (Commissary) Contract", "Authority": "Licensed Commissary", "Cost": "Varies"},
        {"Category": "Zoning", "Requirement": "Itinerant Vendor License", "Authority": "Austin Police Dept", "Cost": "$50"},
        {"Category": "Safety", "Requirement": "Gas Pressure Test", "Authority": "Licensed Plumber", "Cost": "~$150"}
    ]
    st.table(pd.DataFrame(permit_data))

# --- View: Search (Google Drive Integration) ---
elif st.session_state.view == 'search':
    st.title("Google Drive Explorer")
    st.markdown("Enter a business name to locate files shared with your Service Account.")

    user_query = st.text_input("Business Name Search", placeholder="e.g. Acme Corp")

    if user_query:
        with st.spinner(f"Accessing Drive for '{user_query}'..."):
            files = search_drive_files(user_query)
            
            if files:
                st.write(f"Search Results for **{user_query}**:")
                for f in files:
                    m_time = f.get('modifiedTime', '').split('T')[0]
                    is_folder = f.get('mimeType') == 'application/vnd.google-apps.folder'
                    label = "Folder" if is_folder else "File"
                    
                    st.markdown(f"""
                        <div class="file-card">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <img src="{f.get('iconLink')}" width="22px">
                                <a href="{f.get('webViewLink')}" target="_blank" class="file-title">{f.get('name')}</a>
                            </div>
                            <div class="metadata">
                                <span class="status-badge">{label}</span>
                                <span> • Modified: {m_time}</span>
                                <span> • ID: <code>{f.get('id', 'N/A')}</code></span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No matches found. Please ensure the Google Drive folder has been shared with your service account email.")
    else:
        st.info("Results will appear here. Start typing a name above.")
