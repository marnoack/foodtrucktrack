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

# Custom CSS for status badges
st.markdown("""
<style>
    .status-box {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to render the license guide modal
@st.dialog("📜 License & Permit Reference Guide", width="large")
def show_license_directory():
    st.write("Browse common business licenses, requirements, and structural cost breakdowns.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏥 Health", "🚒 Fire Dept", "⚖️ Legal & Reg", "🧱 Zoning & Env"])
    
    with tab1:
        st.subheader("🏥 Health Department")
        st.markdown("**Food Service Establishment Permit**")
        st.caption("Authorizes a business to prepare and serve food to the public. Requires passing a health inspection.")
        st.info("💰 Estimated Cost: $100 – $1,000+ annually (scales based on size).")
        st.divider()
        st.markdown("**Food Handler / Manager Certification**")
        st.caption("Ensures that employees and managers are properly trained in safe food handling practices.")
        st.info("💰 Estimated Cost: $10 – $150 per employee.")
        st.divider()
        st.markdown("**Health and Sanitation Permit**")
        st.caption("Required for personal care businesses (salons, tattoo parlors, spas) to ensure sterilization standards.")
        st.info("💰 Estimated Cost: $50 – $300 annually.")

    with tab2:
        st.subheader("🚒 Fire Department")
        st.markdown("**Fire Department Permit / Certificate of Occupancy**")
        st.caption("Granted after inspection of the building's exits, fire extinguishers, sprinklers, and capacity limits.")
        st.info("💰 Estimated Cost: $50 – $200.")
        st.divider()
        st.markdown("**Hazardous Materials Permit**")
        st.caption("Required if your business stores or handles flammable, toxic, or dangerous chemicals.")
        st.info("💰 Estimated Cost: $100 – $500 annually.")

    with tab3:
        st.subheader("⚖️ Legal & General Regulatory")
        st.markdown("**General Business License**")
        st.caption("A basic license issued by your city or county granting the right to operate a business within local jurisdictions.")
        st.info("💰 Estimated Cost: $50 – $400 annually.")
        st.divider()
        st.markdown("**DBA (Doing Business As) Registration**")
        st.caption("Required if you operate under a name different from your legal entity name or personal name.")
        st.info("💰 Estimated Cost: $10 – $100.")
        st.divider()
        st.markdown("**Sales Tax Permit / Seller's Permit**")
        st.caption("Allows you to collect sales tax on tangible goods sold to consumers on behalf of the state.")
        st.info("💰 Estimated Cost: Generally Free (or nominal registration fee of $10 – $50).")

    with tab4:
        st.subheader("🧱 Zoning & Environment")
        st.markdown("**Zoning Permit / Land Use Permit**")
        st.caption("Verifies that your business activity complies with local layout and regional zoning restrictions.")
        st.info("💰 Estimated Cost: $50 – $300.")
        st.divider()
        st.markdown("**Sign Permit**")
        st.caption("Regulates the size, location, and lighting of outdoor business signs according to city aesthetic codes.")
        st.info("💰 Estimated Cost: $20 – $100.")
        
    st.caption("💡 *Note: Fees vary heavily depending on state, county, and city ordinances.*")

# Application Logic
def main():
    vendors = load_data()
    
    # Sidebar Navigation
    st.sidebar.title("🚚 CompliancePro")
    st.sidebar.markdown("---")
    
    search_query = st.sidebar.text_input("Search Vendors", placeholder="Name or owner...")
    
    filtered_vendors = [
        v for v in vendors 
        if search_query.lower() in v['name'].lower() or search_query.lower() in v['owner'].lower()
    ]
    
    vendor_names = [v['name'] for v in filtered_vendors]
    selected_name = st.sidebar.radio("Select Vendor", vendor_names if vendor_names else ["No results found"])

    # License Directory Action Button in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.write("💡 Need regulatory information?")
    if st.sidebar.button("📜 License Directory Guide", use_container_width=True):
        show_license_directory()

    if not filtered_vendors or selected_name == "No results found":
        st.title("Vendor Compliance Management")
        st.info("Please select a vendor from the sidebar to view detailed compliance records.")
        
        # Summary Overview for Dashboard Home
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Vendors", len(vendors))
        col2.metric("Compliant", "33%", delta="5%")
        col3.metric("Issues Flagged", "2", delta="-1", delta_color="inverse")
        return

    # Vendor Detail View
    vendor = next(v for v in vendors if v['name'] == selected_name)
    
    # Header Section
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

    # Metrics Row
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

    # Document Table
    st.subheader("Document Repository")
    df = pd.DataFrame(vendor['permits'])
    
    # Styled table display
    def style_status(val):
        color = '#d1fae5' if val == 'Approved' else '#fee2e2' if val in ['Expired', 'Missing'] else '#fef3c7'
        text_color = '#065f46' if val == 'Approved' else '#991b1b' if val in ['Expired', 'Missing'] else '#92400e'
        return f'background-color: {color}; color: {text_color}; font-weight: bold; border-radius: 5px'

    st.table(df.style.applymap(style_status, subset=['status']))

    # Management Actions
    with st.expander("Update Records & Notes"):
        note = st.text_area("Audit Notes", placeholder="Enter observations from the latest site visit...")
        uploaded_file = st.file_uploader("Upload New Document", type=['pdf', 'jpg', 'png'])
        if st.button("Submit Update"):
            st.toast("Record updated successfully!", icon="✅")

    # Critical Alerts
    if vendor['status'] == "Expired":
        st.error(f"⚠️ **IMMEDIATE ACTION REQUIRED**: {vendor['name']} has expired critical permits. A 'Stop Service' notice has been drafted.")
        if st.button("Send Formal Notice"):
            st.info("Notice sent to owner email.")

if __name__ == "__main__":
    main()
