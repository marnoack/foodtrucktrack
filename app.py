import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- PRE-FLIGHT CHECK & UI SETUP ---
st.set_page_config(page_title="Truck File Finder", layout="wide")

def check_setup():
    """Validates that secrets and IDs are present before running logic."""
    if "gcp_service_account" not in st.secrets:
        st.error("🛑 **Secret Missing:** I can't find the 'gcp_service_account' in your Streamlit Cloud secrets.")
        st.info("Go to: App Settings -> Secrets -> Paste your JSON here.")
        return False
    
    # Check for the Folder ID
    # You can also put this in your secrets as folder_id: "..."
    if "folder_id" not in st.secrets:
        st.warning("⚠️ **Parent Folder ID Missing:** I don't know which Google Drive folder to look in.")
        return False
    
    return True

def get_drive_service():
    """Initializes the Google Drive API connection."""
    try:
        info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(
            info, 
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Failed to connect to Google Drive: {e}")
        return None

def search_truck(truck_name):
    """Searches for a subfolder and lists its contents."""
    service = get_drive_service()
    if not service: return

    parent_id = st.secrets["folder_id"]
    
    try:
        # 1. Find the folder matching the truck name
        # We search inside the parent_id for folders with the specific name
        query = f"'{parent_id}' in parents and name = '{truck_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        if not folders:
            st.error(f"No folder found for '{truck_name}'. Check spelling or ensure the folder is inside the parent directory.")
            return

        folder_id = folders[0]['id']
        st.success(f"📂 Found Folder: {folders[0]['name']}")

        # 2. List files inside that truck's folder
        file_query = f"'{folder_id}' in parents and trashed = false"
        file_results = service.files().list(q=file_query, fields="files(name, webViewLink, mimeType)").execute()
        files = file_results.get('files', [])

        if not files:
            st.info("This folder is empty.")
        else:
            for f in files:
                # Skip sub-folders for now, just show files
                if f['mimeType'] != 'application/vnd.google-apps.folder':
                    col1, col2 = st.columns([4, 1])
                    col1.markdown(f"**{f['name']}**")
                    col2.link_button("View File", f['webViewLink'])

    except Exception as e:
        st.error(f"Search Error: {e}")

# --- MAIN APP LOGIC ---
st.title("🚚 Food Truck File Finder")

if check_setup():
    truck_name = st.text_input("Enter Truck Name exactly as it appears in Drive:", placeholder="e.g. HILL COUNTRY CULINARY GROUP")
    
    if st.button("Search Files") or truck_name:
        if truck_name:
            search_truck(truck_name)
        else:
            st.warning("Please enter a name to search.")

    # Shared with me debug
    with st.expander("Help! I still don't see anything."):
        email = st.secrets["gcp_service_account"].get("client_email", "unknown")
        st.write("1. **Check Sharing:** Make sure the Google Drive folder is shared with this email:")
        st.code(email)
        st.write("2. **Check Folder ID:** Ensure your 'folder_id' secret matches the long ID in the URL of your main Drive folder.")
