import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from datetime import datetime

# --- CONFIGURATION ---
PARENT_FOLDER_ID = '1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019'

st.set_page_config(page_title="Compliance Portal", layout="wide")

# --- Compliance Data ---
PERMIT_DATA = [
    { "Category": "Health", "Requirement": "Mobile Food Vendor Permit", "Authority": "Austin Public Health", "Cost": 700, "Details": "Annual permit required for all mobile food units." },
    { "Category": "Health", "Requirement": "Food Manager Certificate", "Authority": "ANSI Accredited", "Cost": 100, "Details": "At least one employee must be a certified food manager." },
    { "Category": "Fire Safety", "Requirement": "Fire Inspection", "Authority": "Austin Fire Dept", "Cost": 225, "Details": "Visual inspection of extinguishers and vent hoods." },
    { "Category": "Fire Safety", "Requirement": "Propane Pressure Test", "Authority": "Licensed Plumber", "Cost": 150, "Details": "Required annually for units using liquid propane." },
    { "Category": "Legal", "Requirement": "Texas Sales Tax Permit", "Authority": "TX Comptroller", "Cost": 0, "Details": "Required to collect sales tax on food sales." },
    { "Category": "Legal", "Requirement": "Zoning Approval", "Authority": "City of Austin", "Cost": 0, "Details": "Verified location for food truck operations." }
]

def get_drive_service():
    """Initializes the Google Drive API service using st.secrets."""
    if "google_auth" in st.secrets:
        try:
            info = json.loads(st.secrets["google_auth"])
            creds = service_account.Credentials.from_service_account_info(info)
            scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/drive.readonly'])
            return build('drive', 'v3', credentials=scoped_creds)
        except Exception:
            return None
    return None

def get_files_from_food_truck_folder(truck_name):
    """Finds the subfolder matching truck_name and returns all files within it."""
    service = get_drive_service()
    if not service:
        return []
        
    try:
        # 1. Find the folder named after the food truck within the parent folder
        folder_query = f"name = '{truck_name}' and '{PARENT_FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        folder_results = service.files().list(q=folder_query, fields="files(id)").execute()
        folders = folder_results.get('files', [])
        
        if not folders:
            return []
            
        # 2. Get all files inside that specific truck folder
        truck_folder_id = folders[0]['id']
        file_query = f"'{truck_folder_id}' in parents and trashed = false"
        file_results = service.files().list(
            q=file_query,
            fields="files(id, name, webViewLink, mimeType)",
            pageSize=30
        ).execute()
        
        return file_results.get('files', [])
    except Exception:
        return []

# --- Sidebar ---
st.sidebar.title("Compliance App")
app_mode = st.sidebar.radio("Navigation", ["Requirements", "Documents"])

# --- Main Interface ---
if app_mode == "Requirements":
    st.title("Compliance Requirements")
    
    categories = sorted(list(set(item["Category"] for item in PERMIT_DATA)))
    selected_cat = st.selectbox("Select Category", categories)
    
    filtered_data = [item for item in PERMIT_DATA if item["Category"] == selected_cat]
    
    for req in filtered_data:
        with st.expander(f"{req['Requirement']} — Estimated Cost: ${req['Cost']}"):
            st.write(f"**Authority:** {req['Authority']}")
            st.write(f"**Details:** {req['Details']}")
            
elif app_mode == "Documents":
    st.title("Document Search")
    
    truck_name = st.text_input("Enter Food Truck Name", placeholder="e.g. Tacos El Pastor")
    
    if truck_name:
        with st.spinner(f"Retrieving documents for {truck_name}..."):
            files = get_files_from_food_truck_folder(truck_name)
            
        if files:
            st.write(f"Showing documents for **{truck_name}**:")
            for f in files:
                col1, col2 = st.columns([5, 1])
                icon = "📁" if f['mimeType'] == 'application/vnd.google-apps.folder' else "📄"
                col1.write(f"{icon} {f['name']}")
                if 'webViewLink' in f:
                    col2.markdown(f"[View]({f['webViewLink']})")
        else:
            st.info(f"No folder or documents found for '{truck_name}'.")
            st.caption("Ensure the folder name matches exactly and the service account has access.")
