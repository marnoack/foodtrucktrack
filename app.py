import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime
import json

# --- CONFIGURATION ---
# 1. Open your 'foodtruck' folder in Drive
# 2. Copy the ID from the URL and paste it here:
FOODTRUCK_PARENT_ID = "foodtruck"

# --- Page Configuration ---
st.set_page_config(
    page_title="Food Truck Portal",
    page_icon="🚚",
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
    .metadata { color: #64748b; font-size: 0.85rem; margin-top: 4px; }
    .folder-header {
        background-color: #eff6ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Google Drive Logic ---
def get_drive_service():
    try:
        if "service_account" in st.secrets:
            creds_info = dict(st.secrets["service_account"])
            scopes = ['https://www.googleapis.com/auth/drive.readonly']
            creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
            return build('drive', 'v3', credentials=creds)
        return None
    except Exception as e:
        st.error(f"Authentication Error: {str(e)}")
        return None

def find_truck_folder(truck_name):
    """Finds a folder named after the truck inside the 'foodtruck' parent."""
    service = get_drive_service()
    if not service or not truck_name:
        return None
    
    try:
        # Search for a folder with the name inside the foodtruck parent ID
        query = f"name contains '{truck_name}' and mimeType = 'application/vnd.google-apps.folder' and '{FOODTRUCK_PARENT_ID}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])
        return folders[0] if folders else None
    except Exception as e:
        st.error(f"Error finding folder: {str(e)}")
        return None

def list_files_in_folder(folder_id):
    """Lists all files inside a specific folder ID."""
    service = get_drive_service()
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query, 
            pageSize=30, 
            fields="files(id, name, mimeType, webViewLink, modifiedTime)"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        st.error(f"Error listing files: {str(e)}")
        return []

# --- Sidebar ---
with st.sidebar:
    st.title("Truck Manager")
    st.markdown("---")
    if st.button("🔍 Search by Truck/Firm"): st.session_state.view = 'search'
    if st.button("📊 Global Dashboard"): st.session_state.view = 'dashboard'

# --- App State ---
if 'view' not in st.session_state:
    st.session_state.view = 'search'

# --- Search View ---
if st.session_state.view == 'search':
    st.title("Truck Document Search")
    st.write("Enter the name of the firm or truck to pull up their specific folder from the 'foodtruck' directory.")
    
    truck_input = st.text_input("Truck or Firm Name", placeholder="e.g., Tacos El Pastor")

    if truck_input:
        with st.spinner(f"Locating folder for '{truck_input}'..."):
            folder = find_truck_folder(truck_input)
            
            if folder:
                st.markdown(f"""
                    <div class="folder-header">
                        <h3 style="margin:0;">📂 {folder['name']}</h3>
                        <p style="margin:0; font-size:0.9rem;">Displaying all documents found in this truck's directory.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                files = list_files_in_folder(folder['id'])
                
                if files:
                    for f in files:
                        # Skip folders if any are inside
                        if f['mimeType'] == 'application/vnd.google-apps.folder':
                            continue
                            
                        date = f.get('modifiedTime', '').split('T')[0]
                        st.markdown(f"""
                            <div class="file-card">
                                <a href="{f.get('webViewLink')}" target="_blank" class="file-title">{f.get('name')}</a>
                                <div class="metadata">Last Modified: {date}</div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("This folder is empty.")
            else:
                st.error(f"Could not find a folder matching '{truck_input}' inside the 'foodtruck' directory.")

# --- Dashboard View (Placeholder) ---
elif st.session_state.view == 'dashboard':
    st.title("Compliance Dashboard")
    st.write("Overview of all trucks in the system.")
