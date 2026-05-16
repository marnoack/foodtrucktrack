import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from datetime import datetime

# --- CONFIGURATION ---
PARENT_FOLDER_ID = "1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019"

# Requirement definitions for the checklist
PERMIT_REQUIREMENTS = {
    "Business License": ["license", "business", "registration"],
    "Health Permit": ["health", "sanitary", "inspection"],
    "Fire Safety Certificate": ["fire", "marshal", "extinguisher"],
    "Insurance COI": ["insurance", "coi", "liability"],
    "Seller's Permit": ["seller", "tax", "resale"],
    "Vehicle Registration": ["registration", "dmv", "truck registration"],
    "Commissary Agreement": ["commissary", "kitchen", "agreement"]
}

st.set_page_config(page_title="Food Truck Compliance Portal", layout="wide")

def get_drive_service():
    """Initializes Google Drive service."""
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

def fetch_truck_data(truck_name):
    """Retrieves folder contents and matches them against requirements."""
    service = get_drive_service()
    if not service or not truck_name:
        return None, None
        
    try:
        # 1. Find the truck's specific folder
        folder_query = (
            f"name = '{truck_name}' and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"'{PARENT_FOLDER_ID}' in parents and trashed = false"
        )
        folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
        folders = folder_results.get('files', [])
        
        if not folders:
            return "folder_not_found", None
            
        # 2. Get files from that folder
        target_folder_id = folders[0]['id']
        file_query = f"'{target_folder_id}' in parents and trashed = false"
        file_results = service.files().list(
            q=file_query,
            fields="files(id, name, webViewLink, mimeType, modifiedTime)"
        ).execute()
        
        files = file_results.get('files', [])
        
        # 3. Logic to determine compliance status
        compliance_status = []
        for req, keywords in PERMIT_REQUIREMENTS.items():
            # Check if any file name contains any of the keywords for this requirement
            matched_file = next((f for f in files if any(k in f['name'].lower() for k in keywords)), None)
            compliance_status.append({
                "Requirement": req,
                "Status": "✅ Complete" if matched_file else "❌ Missing",
                "File Name": matched_file['name'] if matched_file else "N/A",
                "Link": matched_file['webViewLink'] if matched_file else None
            })
            
        return files, compliance_status
        
    except Exception as e:
        st.error(f"API Error: {e}")
        return None, None

# --- UI LAYOUT ---
st.title("🚚 Food Truck Compliance & Document Portal")
st.markdown("---")

truck_name_input = st.text_input("Search Food Truck Name", placeholder="e.g. Taco Time")

if truck_name_input:
    files, compliance = fetch_truck_data(truck_name_input)
    
    if files == "folder_not_found":
        st.error(f"No folder found for '{truck_name_input}' in the main directory.")
    elif files is not None:
        # Create Tabs for a clean view
        tab1, tab2 = st.tabs(["📋 Compliance Checklist", "📂 All Documents"])
        
        with tab1:
            st.subheader(f"Compliance Status: {truck_name_input}")
            comp_df = pd.DataFrame(compliance)
            
            # Styling for the table
            def color_status(val):
                color = 'green' if 'Complete' in val else 'red'
                return f'color: {color}; font-weight: bold'

            st.table(comp_df[['Requirement', 'Status', 'File Name']])
            
            # Missing items summary
            missing = [c['Requirement'] for c in compliance if "Missing" in c['Status']]
            if missing:
                st.warning(f"**Missing Items:** {', '.join(missing)}")
            else:
                st.success("All primary documents are present!")

        with tab2:
            st.subheader("Direct File Access")
            if not files:
                st.info("No files found in this folder.")
            else:
                for f in files:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"📄 **{f['name']}**")
                        st.caption(f"Last updated: {f['modifiedTime'][:10]}")
                    with col2:
                        st.link_button("Open", f['webViewLink'])
                    st.divider()

else:
    st.info("Please enter a truck name to check document status.")
    
# Footer
st.sidebar.markdown(f"**Admin Tools**")
st.sidebar.write(f"Connection Status: Active")
st.sidebar.write(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
