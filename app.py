import streamlit as st
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Food Truck Compliance Portal",
    page_icon="🚚",
    layout="wide"
)

# --- MOCK DATA ---
# This dictionary simulates our database of food truck licenses
COMPLIANCE_DATABASE = {
    "HILL COUNTRY CULINARY": [
        {"Document": "Health Department Permit", "Status": "Active", "Expiration": "2024-12-31"},
        {"Document": "Fire Marshal Inspection", "Status": "Active", "Expiration": "2025-05-15"},
        {"Document": "Propane Safety Certificate", "Status": "Expired", "Expiration": "2023-11-01"},
        {"Document": "General Liability Insurance", "Status": "Active", "Expiration": "2024-09-20"},
        {"Document": "Food Manager Certificate", "Status": "Pending", "Expiration": "N/A"}
    ],
    "TACO TRADITION": [
        {"Document": "Health Department Permit", "Status": "Active", "Expiration": "2024-11-15"},
        {"Document": "General Liability Insurance", "Status": "Expired", "Expiration": "2024-01-10"}
    ]
}

def apply_status_style(val):
    """Adds color coding to the Status column."""
    color = 'black'
    if val == 'Active':
        color = '#059669' # Green
    elif val == 'Expired':
        color = '#dc2626' # Red
    elif val == 'Pending':
        color = '#d97706' # Amber
    return f'color: {color}; font-weight: bold'

def main():
    st.title("🚚 Compliance & Licensing Portal")
    st.markdown("Internal system for tracking food truck certifications and expiration dates.")

    # Search Section
    st.divider()
    search_query = st.text_input("Enter Truck Name:", placeholder="e.g., HILL COUNTRY CULINARY").strip().upper()

    if search_query:
        if search_query in COMPLIANCE_DATABASE:
            st.success(f"Records found for **{search_query}**")
            
            # Formatting data for display
            records = COMPLIANCE_DATABASE[search_query]
            df = pd.DataFrame(records)
            
            # Display Metrics
            col1, col2, col3 = st.columns(3)
            active_count = len([r for r in records if r['Status'] == 'Active'])
            expired_count = len([r for r in records if r['Status'] == 'Expired'])
            
            col1.metric("Active Licenses", active_count)
            col2.metric("Expired/Alerts", expired_count, delta_color="inverse")
            col3.metric("Last Audit", datetime.now().strftime("%b %d, %Y"))

            # Styled Table
            st.subheader("License Details")
            styled_df = df.style.applymap(apply_status_style, subset=['Status'])
            st.table(styled_df)

            # Action Area
            st.subheader("Administrative Actions")
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("Download Compliance Report (PDF)"):
                    st.write("Generating report...")
            with action_col2:
                if st.button("Email Expiration Alerts to Owner"):
                    st.write("Alerts sent successfully.")

        else:
            st.error(f"No records found for '{search_query}'. Please check the spelling or contact the administrator.")
    else:
        st.info("Waiting for input... please enter a truck name above to view compliance status.")

    # Sidebar info
    st.sidebar.header("System Status")
    st.sidebar.info("Database: Connected")
    st.sidebar.write(f"Logged in as: Admin_User")

if __name__ == "__main__":
    main()
