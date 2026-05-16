import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import socket
from datetime import datetime

# --- INTERNAL CONFIGURATION ---
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
    if "google_auth" in st.secrets:
        try:
            info = json.loads(st.secrets["google_auth"])
            creds = service_account.Credentials.from_service_account_info(info)
            return build('drive', 'v3', credentials=creds)
        except:
            pass
    return None

def search_files(query):
    service = get_drive_service()
    if service:
        try:
            query_string = f"name contains '{query}' and '{PARENT_FOLDER_ID}' in parents and trashed = false"
            results = service.files().list(
                q=query_string,
                fields="files(id, name, webViewLink)"
            ).execute()
            return results.get('files', [])
        except:
            pass
    return []

# --- Sidebar ---
app_mode = st.sidebar.radio("Navigation", ["Requirements", "Documents"])

# --- Main Interface ---
if app_mode == "Requirements":
    st.title("Compliance Requirements")
    
    categories = sorted(list(set(item["Category"] for item in PERMIT_DATA)))
    selected_cat = st.selectbox("Category", categories)
    
    filtered_data = [item for item in PERMIT_DATA if item["Category"] == selected_cat]
    
    for req in filtered_data:
        with st.expander(f"{req['Requirement']} — ${req['Cost']}"):
            st.write(f"**Authority:** {req['Authority']}")
            st.write(f"**Details:** {req['Details']}")
            
elif app_mode == "Documents":
    st.title("Document Search")
    truck_name = st.text_input("Enter search term", placeholder="Search by name...")
    
    if truck_name:
        files = search_files(truck_name)
        if files:
            for f in files:
                col1, col2 = st.columns([4, 1])
                col1.write(f"📄 {f['name']}")
                if 'webViewLink' in f:
                    col2.markdown(f"[View]({f['webViewLink']})")
        else:
            st.write("No documents found.")
