import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import socket
from datetime import datetime

# --- CONFIGURATION (UNCHANGED) ---
PARENT_FOLDER_ID = '1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019' 

st.set_page_config(page_title="Austin Food Truck Compliance", layout="wide")

# --- NAVIGATION LOGIC ---
if 'page' not in st.session_state:
    st.session_state.page = 'Requirements'

def set_page(page_name):
    st.session_state.page = page_name

# Sidebar for Navigation
with st.sidebar:
    st.title("🚛 Mobile Food Admin")
    st.button("📋 Permit Requirements", on_click=set_page, args=('Requirements',), use_container_width=True)
    st.button("📂 Digital Document Locker", on_click=set_page, args=('Locker',), use_container_width=True)
    st.divider()
    st.caption(f"System Parent ID: `{PARENT_FOLDER_ID[:8]}...`")

# --- GOOGLE DRIVE LOGIC (UNCHANGED) ---

def get_gdrive_service():
    try:
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        st.error(f"❌ Connection Error: {e}. Check Streamlit Secrets.")
        st.stop()

def find_truck_folder(service, truck_name):
    query = (f"name = '{truck_name}' and "
             f"'{PARENT_FOLDER_ID}' in parents and "
             f"mimeType = 'application/vnd.google-apps.folder' and "
             f"trashed = false")
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def list_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name, modifiedTime, webViewLink)').execute()
    return results.get('files', [])

# --- PAGE ROUTING ---

if st.session_state.page == 'Requirements':
    # NEW: Austin Texas Permit Guide
    st.title("📋 Austin Food Truck Permit Requirements")
    st.markdown("Below are the mandatory permits and licenses required to operate a food truck in Austin, Texas.")

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.expander("1. Austin Public Health (APH) Permit", expanded=True):
            st.markdown("""
            **Permit Name:** Mobile Food Establishment (MFE) Permit.
            - **Application:** Must submit a completed APH application and fee.
            - **Inspection:** A physical inspection of the unit is required.
            - **Central Preparation Facility (CPF):** You must provide a signed contract with a licensed commissary.
            - [Official APH Website](https://www.austintexas.gov/department/mobile-food-establishments)
            """)

        with st.expander("2. Fire Marshal Inspection (AFD)"):
            st.markdown("""
            **Requirement:** Annual safety inspection by the Austin Fire Department.
            - **Propane:** Requires a specific pressure test.
            - **Fire Suppression:** Vent hoods must be inspected and tagged.
            - **Extinguishers:** Must have 2A10BC and Class K (if using grease).
            """)

        with st.expander("3. State of Texas Sales Tax Permit"):
            st.markdown("""
            **Requirement:** Issued by the Texas Comptroller's Office.
            - Necessary to collect and remit sales tax.
            - Must be displayed prominently on the truck.
            """)

        with st.expander("4. Food Manager Certificate"):
            st.markdown("""
            **Requirement:** At least one person in charge must have a City of Austin Food Manager Certificate.
            - All other employees must have a Basic Food Handler registration.
            """)

    with col2:
        st.info("💡 **Compliance Tip**")
        st.write("Ensure your CPF (Commissary) is in good standing before applying for your APH permit, as they will verify the facility license.")
        st.image("https://www.austintexas.gov/sites/default/files/styles/standard_listing/public/images/Health_0.png?itok=Mh7rZ7iO", width=150)

elif st.session_state.page == 'Locker':
    # ORIGINAL: Document Locker logic
    st.title("📂 Digital Document Locker")
    st.markdown("Search for your truck folder in Google Drive to verify uploaded compliance docs.")

    search_query = st.text_input("Truck Folder Name:", placeholder="e.g., HILL COUNTRY CULINARY")

    if search_query:
        service = get_gdrive_service()
        with st.spinner("Searching Google Drive..."):
            folder_id = find_truck_folder(service, search_query)
        
        if folder_id:
            files = list_files_in_folder(service, folder_id)
            if files:
                data = [{
                    "Document": f['name'],
                    "Last Sync": f['modifiedTime'][:10],
                    "Drive Link": f['webViewLink']
                } for f in files]
                
                st.dataframe(
                    pd.DataFrame(data),
                    use_container_width=True,
                    column_config={"Drive Link": st.column_config.LinkColumn()}
                )
            else:
                st.info("Folder found, but no files were detected inside.")
        else:
            st.error(f"Folder '{search_query}' not found in the parent directory.")
