import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import socket
from datetime import datetime

# UI Configuration
st.set_page_config(page_title="Austin Food Truck Compliance", layout="wide")

# --- Compliance Data ---
permit_data = [
    { "Category": "Health", "Requirement": "Mobile Food Vendor Permit", "Authority": "Austin Public Health", "Cost": 700 },
    { "Category": "Fire Safety", "Requirement": "Fire Inspection", "Authority": "Austin Fire Dept", "Cost": 225 },
    { "Category": "Fire Safety", "Requirement": "Propane Pressure Test", "Authority": "Licensed Plumber", "Cost": 150 },
    { "Category": "Legal", "Requirement": "Texas Sales Tax Permit", "Authority": "TX Comptroller", "Cost": 0 }
]

# --- Google Drive Logic ---
def get_drive_service():
    # Using the imports you provided to build the service
    if "google_auth" in st.secrets:
        info = json.loads(st.secrets["google_auth"])
        creds = service_account.Credentials.from_service_account_info(info)
        return build('drive', 'v3', credentials=creds)
    return None

def search_files(query):
    service = get_drive_service()
    if service:
        # Search for files matching the name
        results = service.files().list(
            q=f"name contains '{query}' and trashed = false",
            fields="files(id, name)"
        ).execute()
        return results.get('files', [])
    return []

# --- App Interface ---
st.title("🚚 Austin Food Truck Compliance Hub")

# Search Section
search_query = st.text_input("Search for Food Truck Documents", placeholder="Enter truck name...")
if search_query:
    files = search_files(search_query)
    if files:
        for f in files:
            st.write(f"Found: {f['name']} (ID: {f['id']})")
    else:
        st.info("No documents found.")

st.divider()

# Requirements Table
st.header("General City Requirements")
df = pd.DataFrame(permit_data)
st.table(df)

# Footer info using your imports
st.caption(f"Checked on: {datetime.now().strftime('%Y-%m-%d')} | Node: {socket.gethostname()}")
