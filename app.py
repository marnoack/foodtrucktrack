import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- CONFIGURATION ---
# 1. Open your 'foodtruck' folder in a browser. 
# 2. Copy the long string of letters/numbers at the end of the URL.
# 3. Paste it here:
PARENT_FOLDER_ID = "1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019" 

st.set_page_config(page_title="Truck Finder Debug", layout="wide")

def get_drive_service():
    """Initializes service with your specific secret key."""
    try:
        # Check if secrets exist
        if "gcp_service_account" not in st.secrets:
            st.error("Error: 'gcp_service_account' key missing from Streamlit Secrets.")
            return None
        
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        # Add scopes explicitly just in case
        scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/drive.readonly'])
        return build('drive', 'v3', credentials=scoped_credentials)
    except Exception as e:
        st.error(f"Authentication Setup Failed: {e}")
        return None

def debug_list_all_visible():
    """Diagnostic: Shows every single folder the Service Account can see."""
    service = get_drive_service()
    if not service: return
    
    st.write("### 🔍 Diagnostic: All Visible Folders")
    try:
        # We query for ALL folders without parent constraints first to see if permissions are working
        results = service.files().list(
            q="mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name, parents)",
            pageSize=50
        ).execute()
        folders = results.get('files', [])
        
        if not folders:
            st.warning("The Service Account cannot see ANY folders. Did you share the folder with the Service Account email address?")
            # Display the email for easy copying
            if "client_email" in st.secrets["gcp_service_account"]:
                email = st.secrets["gcp_service_account"]["client_email"]
                st.info(f"Please share your Google Drive folder with: `{email}`")
        else:
            st.write(f"The Service Account sees {len(folders)} folders:")
            st.table(folders)
    except Exception as e:
        st.error(f"API Call Failed: {e}")

def find_files_in_truck(truck_name):
    """Deep search for the specific truck folder."""
    service = get_drive_service()
    if not service: return
    
    # Cleaning the search term
    search_term = truck_name.strip()
    
    # Look specifically inside the parent folder
    query = f"'{PARENT_FOLDER_ID}' in parents and trashed = false"
    
    try:
        results = service.files().list(q=query, fields="files(id, name, mimeType, webViewLink)").execute()
        items = results.get('files', [])
        
        # Find folder by name (case-insensitive)
        target_folder = next((f for f in items if f['name'].lower() == search_term.lower() and f['mimeType'] == 'application/vnd.google-apps.folder'), None)
        
        if target_folder:
            st.success(f"✅ Found Folder: {target_folder['name']}")
            # Now list files inside THAT folder
            file_results = service.files().list(
                q=f"'{target_folder['id']}' in parents and trashed = false",
                fields="files(name, webViewLink, mimeType)"
            ).execute()
            
            files = file_results.get('files', [])
            if not files:
                st.info("This folder is empty.")
            else:
                for f in files:
                    if f['mimeType'] != 'application/vnd.google-apps.folder':
                        col1, col2 = st.columns([3, 1])
                        col1.write(f"📄 {f['name']}")
                        col2.link_button("Open", f['webViewLink'])
        else:
            st.error(f"Could not find a folder named '{search_term}' inside the parent folder.")
            st.write("Folders actually found inside parent:")
            st.json([f['name'] for f in items if f['mimeType'] == 'application/vnd.google-apps.folder'])
            
    except Exception as e:
        st.error(f"Search error: {e}")

# --- MAIN UI ---
st.title("🚚 Food Truck File Manager")

truck_input = st.text_input("Truck Name (e.g., HILL COUNTRY CULINARY GROUP)", "")

if truck_input:
    find_files_in_truck(truck_input)

st.divider()
with st.expander("🛠️ Connection Debugger (Click if it's not working)"):
    debug_list_all_visible()
