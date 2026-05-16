import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from datetime import datetime

# --- CONFIGURATION ---
# Parent folder ID where all individual food truck folders are located
PARENT_FOLDER_ID = "1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019" 

st.set_page_config(page_title="Food Truck Document Portal", layout="wide")

def get_drive_service():
    """Initializes the Google Drive API service using st.secrets."""
    if "google_auth" in st.secrets:
        try:
            info = json.loads(st.secrets["google_auth"])
            creds = service_account.Credentials.from_service_account_info(info)
            scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/drive.readonly'])
            return build('drive', 'v3', credentials=scoped_creds)
        except Exception as e:
            st.error(f"Authentication Error: {e}")
            return None
    return None

def get_truck_documents(truck_name):
    """
    1. Finds the folder named exactly after the truck inside the PARENT_FOLDER_ID.
    2. Retrieves all files from inside that specific folder.
    """
    service = get_drive_service()
    if not service or not truck_name:
        return None
        
    try:
        # STEP 1: Search for the folder with the name of the food truck inside the parent folder
        folder_query = (
            f"name = '{truck_name}' and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"'{PARENT_FOLDER_ID}' in parents and "
            f"trashed = false"
        )
        
        folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
        folders = folder_results.get('files', [])
        
        if not folders:
            return "folder_not_found"
            
        # STEP 2: Use the ID of the found folder to find its contents
        target_folder_id = folders[0]['id']
        file_query = f"'{target_folder_id}' in parents and trashed = false"
        
        file_results = service.files().list(
            q=file_query,
            fields="files(id, name, webViewLink, mimeType, modifiedTime)",
            pageSize=100
        ).execute()
        
        return file_results.get('files', [])
    except Exception as e:
        st.error(f"Error accessing Drive: {e}")
        return None

# --- Main Interface ---
st.title("🚚 Food Truck Document Retrieval")
st.write(f"Updated as of: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

truck_name_input = st.text_input("Enter Food Truck Name:", placeholder="Match the folder name exactly...")

if truck_name_input:
    with st.spinner(f"Searching for '{truck_name_input}' folder..."):
        results = get_truck_documents(truck_name_input)
        
    if results == "folder_not_found":
        st.warning(f"Could not find a folder named '{truck_name_input}' inside the master directory.")
    elif results is not None:
        if len(results) > 0:
            st.success(f"Found {len(results)} documents for {truck_name_input}")
            
            # Convert to DataFrame for a clean table view using pandas
            df = pd.DataFrame(results)
            df['Last Modified'] = pd.to_datetime(df['modifiedTime']).dt.strftime('%Y-%m-%d')
            
            # Displaying files
            for _, row in df.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    col1.markdown(f"**{row['name']}** \n*Modified: {row['Last Modified']}*")
                    if 'webViewLink' in row:
                        col2.link_button("View Document", row['webViewLink'])
                    st.divider()
        else:
            st.info(f"The folder '{truck_name_input}' exists but is currently empty.")
