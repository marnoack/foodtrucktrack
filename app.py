import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import socket
from datetime import datetime

# --- CONFIGURATION ---
PARENT_FOLDER_ID = '1Mk_xL9MwI036YOk9W1vAJ5K2RCNy1019'

st.set_page_config(page_title="Austin Food Truck Compliance", layout="wide", page_icon="🚛")

# --- THE DATA (RESTORED FROM GITHUB SNIPPET) ---
permit_data = [
    { 
        "Category": "Health", 
        "Requirement": "Mobile Food Vendor Permit", 
        "Authority": "Austin Public Health", 
        "Frequency": "Annual", 
        "Est. Cost": 700,
        "Details": "Primary permit required for all units."
    },
    { 
        "Category": "Fire Safety", 
        "Requirement": "Mobile Food Unit Fire Inspection", 
        "Authority": "Austin Fire Dept (AFD)", 
        "Frequency": "Annual", 
        "Est. Cost": 225,
        "Details": "Required for units using propane or electric heating."
    },
    { 
        "Category": "Legal", 
        "Requirement": "Texas Sales Tax Permit", 
        "Authority": "TX Comptroller", 
        "Frequency": "Once", 
        "Est. Cost": 0,
        "Details": "Required to collect sales tax on food items."
    },
    { 
        "Category": "Health", 
        "Requirement": "Food Manager Certificate", 
        "Authority": "ANSI Accredited", 
        "Frequency": "Every 5 Years", 
        "Est. Cost": 50,
        "Details": "One person on staff must have this certification."
    },
    { 
        "Category": "Operations", 
        "Requirement": "Central Preparation Facility (CPF) Contract", 
        "Authority": "Licensed Commissary", 
        "Frequency": "Monthly", 
        "Est. Cost": 500,
        "Details": "Agreement with a licensed kitchen for waste and prep."
    },
    { 
        "Category": "Zoning", 
        "Requirement": "Itinerant Vendor License", 
        "Authority": "Austin Police Dept", 
        "Frequency": "Annual", 
        "Est. Cost": 50,
        "Details": "Verification for operating in specific public right-of-ways."
    },
    { 
        "Category": "Fire Safety", 
        "Requirement": "Propane System Pressure Test", 
        "Authority": "Licensed Plumber", 
        "Frequency": "Annual", 
        "Est. Cost": 150,
        "Details": "Proof that your gas lines are leak-free."
    },
    { 
        "Category": "Health", 
        "Requirement": "Food Handler Certificate", 
        "Authority": "State Approved", 
        "Frequency": "Every 2 Years", 
        "Est. Cost": 10,
        "Details": "Required for all employees handling food."
    }
]

# --- SESSION STATE & NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'Requirements'

def set_page(page_name):
    st.session_state.page = page_name

with st.sidebar:
    st.title("🚛 Food Truck Admin")
    st.button("📋 Permit Requirements", on_click=set_page, args=('Requirements',), use_container_width=True)
    st.button("📂 Digital Document Locker", on_click=set_page, args=('Locker',), use_container_width=True)
    st.divider()
    st.caption(f"Last Accessed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption(f"Host: {socket.gethostname()}")

# --- GOOGLE DRIVE HELPER FUNCTIONS ---
def get_gdrive_service():
    try:
        # Assumes streamlit secrets are configured with service account info
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        st.error(f"❌ Google Drive Auth Error: {e}")
        st.info("Please ensure 'gcp_service_account' is set in Streamlit Secrets.")
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

# --- PAGE RENDERING ---

if st.session_state.page == 'Requirements':
    st.title("📋 Austin Permit Requirements")
    st.info("Below is the regulatory roadmap for operating a mobile food unit in Austin, TX.")
    
    df = pd.DataFrame(permit_data)
    
    # Financial Overview Metrics
    col1, col2, col3 = st.columns(3)
    annual_fees = df[df['Frequency'].isin(['Annual', 'Every 2 Years', 'Every 5 Years'])]['Est. Cost'].sum()
    monthly_fees = df[df['Frequency'] == 'Monthly']['Est. Cost'].sum()
    
    col1.metric("Annualized Regulatory Fees", f"${annual_fees:,.2f}")
    col2.metric("Monthly Recurring (CPF)", f"${monthly_fees:,.2f}")
    col3.metric("Permit Count", len(df))

    st.divider()

    # Data Table with Formatting
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Est. Cost": st.column_config.NumberColumn(format="$%d"),
            "Requirement": st.column_config.TextColumn(help="Official name of the permit/certification"),
            "Details": st.column_config.TextColumn(width="large")
        }
    )

elif st.session_state.page == 'Locker':
    st.title("📂 Digital Document Locker")
    st.write("Access your cloud-stored compliance documents directly from Google Drive.")

    truck_name = st.text_input("Enter Truck Name (Folder Name):", placeholder="e.g. HILL COUNTRY CULINARY")

    if truck_name:
        service = get_gdrive_service()
        with st.spinner(f"Accessing folder: {truck_name}..."):
            folder_id = find_truck_folder(service, truck_name)
            
            if folder_id:
                files = list_files_in_folder(service, folder_id)
                if files:
                    st.success(f"Found {len(files)} documents.")
                    
                    # Transform for display
                    file_list = []
                    for f in files:
                        file_list.append({
                            "Document Name": f['name'],
                            "Modified": f['modifiedTime'][:10],
                            "View": f['webViewLink']
                        })
                    
                    st.table(pd.DataFrame(file_list))
                else:
                    st.warning("Folder found, but it is currently empty.")
            else:
                st.error(f"No folder named '{truck_name}' found in the system root.")
