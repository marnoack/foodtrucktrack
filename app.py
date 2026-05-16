import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import socket
from datetime import datetime

# --- CONFIGURATION ---
# The ID of the parent folder containing all food truck folders
PARENT_FOLDER_ID = '1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019'
#PARENT_FOLDER_ID = '1tFAdApE1DwQpgvxh0CKU_3j5UfHhh5PH'

st.set_page_config(page_title="Gestión de Cumplimiento", layout="wide")

# --- GOOGLE DRIVE LOGIC ---

def get_gdrive_service():
    """Authenticates and returns the Google Drive service."""
    try:
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        st.error(f"❌ configuration Error: {e}")
        st.stop()

def find_truck_folder(service, truck_name):
    """Searches for a folder matching the truck name inside the parent folder."""
    query = (f"name = '{truck_name}' and "
             f"'{PARENT_FOLDER_ID}' in parents and "
             f"mimeType = 'application/vnd.google-apps.folder' and "
             f"trashed = false")
    
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def list_files_in_folder(service, folder_id):
    """Lists all files in the specific truck's folder."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name, modifiedTime, webViewLink)').execute()
    return results.get('files', [])

# --- DATA PROCESSING ---

def apply_status_style(val):
    """Styles the compliance status."""
    if val == 'Active': return 'color: #059669; font-weight: bold'
    if val == 'Expired': return 'color: #dc2626; font-weight: bold'
    return ''

# --- MAIN APP UI ---

st.title("🚚 Food Truck Compliance Portal")
st.markdown("Search for a truck to view its digital document locker from Google Drive.")

# Search Input
search_query = st.text_input("Enter Truck Name (e.g., HILL COUNTRY CULINARY):", placeholder="Exact name of the folder in Drive")

if search_query:
    service = get_gdrive_service()
    
    with st.spinner(f"Searching for '{search_query}' folder..."):
        folder_id = find_truck_folder(service, search_query)
        
    if folder_id:
        st.success(f"✅ Folder found for **{search_query}**")
        
        # Fetch files from that folder
        files = list_files_in_folder(service, folder_id)
        
        if files:
            # Create a dataframe for display
            data = []
            for f in files:
                # Mock compliance logic based on file name or date
                # In a real app, you might parse the 'modifiedTime'
                is_expired = "expired" in f['name'].lower()
                
                data.append({
                    "Document Name": f['name'],
                    "Last Updated": f['modifiedTime'].split('T')[0],
                    "Status": "Expired" if is_expired else "Active",
                    "Link": f['webViewLink']
                })
            
            df = pd.DataFrame(data)
            
            # Display Metrics
            c1, c2 = st.columns(2)
            c1.metric("Total Documents", len(df))
            c2.metric("Expired Alerts", len(df[df['Status'] == 'Expired']))

            # Display interactive table
            st.subheader("Digital Document Locker")
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "Link": st.column_config.LinkColumn("View in Drive")
                }
            )
            
        else:
            st.warning("The folder was found, but it is currently empty.")
    else:
        st.error(f"No folder named '{search_query}' was found in the parent directory.")

# Sidebar info
st.sidebar.header("System Settings")
st.sidebar.write(f"Parent Folder: `{PARENT_FOLDER_ID}`")
if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
