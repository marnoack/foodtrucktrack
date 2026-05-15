import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- CONFIGURATION ---
# IMPORTANT: Ensure your Service Account email is added as a 'Viewer' 
# to this specific folder in Google Drive.
FOODTRUCK_PARENT_ID = "1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019"

st.set_page_config(page_title="Truck Manager", page_icon="🚚", layout="wide")

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
    service = get_drive_service()
    if not service or not truck_name:
        return None
    
    try:
        # We use 'contains' which is more flexible than '=' 
        # Note: API queries are case-sensitive. We search for the exact string provided.
        query = (
            f"mimeType = 'application/vnd.google-apps.folder' "
            f"and '{FOODTRUCK_PARENT_ID}' in parents "
            f"and name contains '{truck_name}' "
            f"and trashed = false"
        )
        
        results = service.files().list(
            q=query, 
            fields="files(id, name)",
            spaces='drive'
        ).execute()
        
        folders = results.get('files', [])
        
        # If no exact match, try a broader search of ALL subfolders to find a case-insensitive match manually
        if not folders:
            all_subfolders_query = f"'{FOODTRUCK_PARENT_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            all_results = service.files().list(q=all_subfolders_query, fields="files(id, name)").execute()
            all_folders = all_results.get('files', [])
            
            # Manual case-insensitive check
            for f in all_folders:
                if truck_name.lower() in f['name'].lower():
                    return f
                    
        return folders[0] if folders else None
    except Exception as e:
        st.error(f"Search Error: {str(e)}")
        return None

def list_files_in_folder(folder_id):
    service = get_drive_service()
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query, 
            fields="files(id, name, mimeType, webViewLink, modifiedTime)"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        st.error(f"File List Error: {str(e)}")
        return []

# --- Sidebar Diagnostics ---
with st.sidebar:
    st.title("Settings & Tools")
    st.info(f"Current Parent ID: {FOODTRUCK_PARENT_ID}")
    
    if st.button("🛠 Test Connection"):
        service = get_drive_service()
        if service:
            try:
                folder_meta = service.files().get(fileId=FOODTRUCK_PARENT_ID, fields='name').execute()
                st.success(f"Connected! Can see: {folder_meta['name']}")
            except Exception as e:
                st.error("Cannot access parent folder. Check Permissions.")
    
    st.markdown("---")
    st.caption("Tip: Add the Service Account email to the 'foodtruck' folder 'Share' settings.")

# --- Main UI ---
st.title("🚚 Food Truck Document Portal")

search_query = st.text_input("Enter Truck or Firm Name", placeholder="e.g. HILL COUNTRY CULINARY GROUP")

if search_query:
    with st.spinner("Searching..."):
        folder = find_truck_folder(search_query)
        
        if folder:
            st.success(f"Found Folder: **{folder['name']}**")
            files = list_files_in_folder(folder['id'])
            
            if files:
                for f in files:
                    if f['mimeType'] == 'application/vnd.google-apps.folder': continue
                    
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{f['name']}**")
                            st.caption(f"Modified: {f.get('modifiedTime', 'N/A')}")
                        with col2:
                            st.link_button("Open", f['webViewLink'])
                        st.divider()
            else:
                st.warning("No files found inside this folder.")
        else:
            st.error(f"No folder found for '{search_query}'.")
            st.markdown("""
            **Troubleshooting Steps:**
            1. **Permissions:** Open Drive, right-click the 'foodtruck' folder -> Share -> Add your Service Account email (from your JSON secrets) as **Viewer**.
            2. **Folder ID:** Ensure the ID in the code matches the ID in your browser URL when you are inside the 'foodtruck' folder.
            3. **Sub-folders:** Ensure the folder is directly inside 'foodtruck' and not nested deeper.
            """)
