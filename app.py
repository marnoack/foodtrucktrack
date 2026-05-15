import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="Austin Food Truck Permit Tracker",
    page_icon="🚚",
    layout="wide"
)

# Application Title and Description
st.title("🚚 Austin Mobile Food Vendor Permit Tracker")
st.markdown("""
This application tracks the essential permits, licenses, and inspections required to operate a food truck 
within the **City of Austin** and **Travis County**.
""")

# The Data
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

df = pd.DataFrame(permit_data)

# Sidebar Filters
st.sidebar.header("Filter Requirements")

# Filter by Category
categories = ["All"] + sorted(df["Category"].unique().tolist())
selected_category = st.sidebar.selectbox("Select Category", categories)

# Filter by Authority
authorities = ["All"] + sorted(df["Authority"].unique().tolist())
selected_authority = st.sidebar.selectbox("Select Authority", authorities)

# Search Box
search_query = st.sidebar.text_input("Search Requirement", "")

# Apply Logic
filtered_df = df.copy()

if selected_category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == selected_category]

if selected_authority != "All":
    filtered_df = filtered_df[filtered_df["Authority"] == selected_authority]

if search_query:
    filtered_df = filtered_df[filtered_df["Requirement"].str.contains(search_query, case=False)]

# Dashboard Layout
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Requirements", len(filtered_df))
with col2:
    total_est = filtered_df["Est. Cost"].sum()
    st.metric("Total Estimated Initial Cost", f"${total_est:,.2f}")
with col3:
    unique_depts = filtered_df["Authority"].nunique()
    st.metric("Departments Involved", unique_depts)

# Main Table Display
st.subheader("Permit List")

# Formatting for the table
def highlight_category(val):
    colors = {
        'Health': 'background-color: #d1fae5; color: #065f46',
        'Fire Safety': 'background-color: #fee2e2; color: #991b1b',
        'Legal': 'background-color: #f3e8ff; color: #6b21a8',
        'Operations': 'background-color: #fef3c7; color: #92400e',
        'Zoning': 'background-color: #dbeafe; color: #1e40af'
    }
    return colors.get(val, '')

# Using st.dataframe for an interactive experience
st.dataframe(
    filtered_df,
    column_config={
        "Est. Cost": st.column_config.NumberColumn(format="$%d"),
        "Requirement": st.column_config.TextColumn(width="medium"),
        "Details": st.column_config.TextColumn(width="large"),
    },
    hide_index=True,
    use_container_width=True
)

# Help Section
with st.expander("📌 Need Help? Next Steps for Austin Vendors"):
    st.write("""
    1. **Contact Austin Public Health**: Visit the Environmental Health Services Division.
    2. **Get a Commissary**: You must have a signed Central Preparation Facility contract before applying for a health permit.
    3. **Schedule Inspections**: Fire inspections are conducted at the Rutherford Lane Campus.
    4. **Register with the State**: Ensure you have your Sales and Use Tax permit through the Texas Comptroller.
    """)

st.caption("Disclaimer: This list is for informational purposes. Costs and requirements are subject to change by local authorities.")