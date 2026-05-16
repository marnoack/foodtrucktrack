import streamlit as st
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="CompliancePro Dashboard",
    page_icon="🚚",
    layout="wide"
)

# Mock Data
def load_data():
    return [
        {
            "id": "1",
            "name": "The Rolling Taco",
            "owner": "Maria Garcia",
            "status": "Incomplete",
            "last_audit": "2024-05-10",
            "score": 65,
            "permits": [
                {"document": "Business License", "status": "Approved", "expiry": "2025-01-15"},
                {"document": "Health Dept Permit", "status": "Pending", "expiry": "2024-06-20"},
                {"document": "Fire Safety Cert", "status": "Missing", "expiry": "N/A"},
                {"document": "Food Handler Cards", "status": "Approved", "expiry": "2024-12-01"}
            ]
        },
        {
            "id": "2",
            "name": "Burger Galaxy",
            "owner": "John Smith",
            "status": "Compliant",
            "last_audit": "2024-05-15",
            "score": 98,
            "permits": [
                {"document": "Business License", "status": "Approved", "expiry": "2025-03-22"},
                {"document": "Health Dept Permit", "status": "Approved", "expiry": "2025-05-01"},
                {"document": "Fire Safety Cert", "status": "Approved", "expiry": "2024-11-15"},
                {"document": "Food Handler Cards", "status": "Approved", "expiry": "2025-01-10"}
            ]
        },
        {
            "id": "3",
            "name": "Sushi Stop",
            "owner": "Kenji Sato",
            "status": "Expired",
            "last_audit": "2024-04-20",
            "score": 42,
            "permits": [
                {"document": "Business License", "status": "Expired", "expiry": "2024-04-01"},
                {"document": "Health Dept Permit", "status": "Approved", "expiry": "2024-09-12"},
                {"document": "Fire Safety Cert", "status": "Approved", "expiry": "2024-12-30"},
                {"document": "Food Handler Cards", "status": "Approved", "expiry": "2024-10-15"}
            ]
        }
    ]

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    vendors = load_data()
    
    # Sidebar
    st.sidebar.title("🚚 CompliancePro")
    st.sidebar.markdown("---")
    
    search_query = st.sidebar.text_input("Search Vendors", placeholder="Name or owner...")
    
    filtered_vendors = [
        v for v in vendors 
        if search_query.lower() in v['name'].lower() or search_query.lower() in v['owner'].lower()
    ]
    
    vendor_names = [v['name'] for v in filtered_vendors]
    selected_name = st.sidebar.radio("Select Vendor", vendor_names if vendor_names else ["No results found"])

    if not filtered_vendors or selected_name == "No results found":
        st.title("Vendor Compliance Management")
        st.info("Please select a vendor from the sidebar.")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Vendors", len(vendors))
        return

    # Vendor Detail View
    vendor = next(v for v in vendors if v['name'] == selected_name)
    
    # Header
    col_title, col_status = st.columns([3, 1])
    with col_title:
        st.title(vendor['name'])
        st.caption(f"Owner: {vendor['owner']} | Last Audit: {vendor['last_audit']}")
    
    with col_status:
        if vendor['status'] == "Compliant":
            st.success(f"Status: {vendor['status']}")
        elif vendor['status'] == "Expired":
            st.error(f"Status: {vendor['status']}")
        else:
            st.warning(f"Status: {vendor['status']}")

    st.markdown("---")

    # Metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Compliance Score", f"{vendor['score']}%")
        st.markdown('</div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Documents Tracked", len(vendor['permits']))
        st.markdown('</div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        missing = len([p for p in vendor['permits'] if p['status'] in ["Missing", "Expired"]])
        st.metric("Action Items", missing)
        st.markdown('</div>', unsafe_allow_html=True)

    # Document Table with Fix for applymap error
    st.subheader("Document Repository")
    df = pd.DataFrame(vendor['permits'])
    
    def style_status(val):
        if val == 'Approved':
            return 'background-color: #d1fae5; color: #065f46'
        elif val in ['Expired', 'Missing']:
            return 'background-color: #fee2e2; color: #991b1b'
        return 'background-color: #fef3c7; color: #92400e'

    # Using map (Pandas 2.0+) and column styling
    styled_df = df.style.map(style_status, subset=['status'])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Management Actions
    with st.expander("Update Records & Notes"):
        st.text_area("Audit Notes")
        st.file_uploader("Upload New Document", type=['pdf', 'jpg', 'png'])
        if st.button("Submit Update"):
            st.toast("Record updated successfully!")

if __name__ == "__main__":
    main()
