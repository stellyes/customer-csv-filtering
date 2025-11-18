import streamlit as st
import pandas as pd
import io

# Page config
st.set_page_config(
    page_title="CSV Filter Tool",
    page_icon="🔍",
    layout="centered"
)

# Title and description
st.title("🔍 CSV Filter Tool")
st.markdown("Upload a CSV file to filter out test/canceled entries and invalid driver's licenses")

# Initialize session state
if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = None
if 'excluded_df' not in st.session_state:
    st.session_state.excluded_df = None
if 'original_df' not in st.session_state:
    st.session_state.original_df = None

# File upload
uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

if uploaded_file is not None:
    try:
        # Read the CSV
        df = pd.read_csv(uploaded_file, dtype=str)
        df = df.fillna("")
        st.session_state.original_df = df
        
        # Validate required columns
        required_cols = ['First Name', 'Last Name', 'Customer Drivers License', 'Customer ID', 
                        'Gender', 'Date of Birth', 'Email', 'Opted In', 'Phone', 
                        'Street Address', 'City', 'State', 'Zip Code', 
                        'Reward Points ($) Balance', 'Customer Source',
                        'Customer Drivers License Expiration Date', 'Medical Id',
                        'Customer Medical Id Expiration Date', 'Customer Profile Notes', 'Banned']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
            st.info(f"📋 Available columns: {', '.join(df.columns.tolist())}")
        else:
            st.success(f"✅ File uploaded successfully: {len(df)} rows")
            
            # Show original data preview
            with st.expander("📄 Preview Original Data (first 5 rows)"):
                st.dataframe(df.head())
            
            # Filter button
            if st.button("🔍 Apply Filters", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    # Apply filters
                    mask = (
                        ~df["First Name"].str.contains(
                            "canceled|cancelled|test|testing|customer", 
                            case=False, 
                            na=False,
                            regex=True
                        ) &
                        ~df["Last Name"].str.contains(
                            "canceled|cancelled|test|testing|customer", 
                            case=False, 
                            na=False,
                            regex=True
                        ) &
                        (df["Customer Drivers License"].str.strip().str.upper() != "N/A") &
                        (df["Customer Drivers License"].str.strip() != "")
                    )
                    
                    # Split into filtered and excluded
                    filtered_df = df[mask].copy()
                    excluded_df = df[~mask].copy()
                    
                    # Format filtered data with new column structure
                    formatted_df = pd.DataFrame()
                    formatted_df['external ID'] = filtered_df['Customer ID']
                    formatted_df['First Name'] = filtered_df['First Name']
                    formatted_df['Last Name'] = filtered_df['Last Name']
                    formatted_df['Gender'] = filtered_df['Gender']
                    formatted_df['Date of Birth'] = filtered_df['Date of Birth']
                    formatted_df['Email'] = filtered_df['Email']
                    formatted_df['Email Opt-In'] = filtered_df['Opted In']
                    formatted_df['Phone'] = filtered_df['Phone']
                    formatted_df['SMS Opt-In'] = 'N'
                    formatted_df['Push Opt-In'] = 'N'
                    
                    # Combine Street Address and City for Address column
                    formatted_df['Address'] = filtered_df['Street Address'] + ', ' + filtered_df['City']
                    
                    formatted_df['State'] = filtered_df['State']
                    formatted_df['Zip'] = filtered_df['Zip Code']
                    formatted_df['Minimum Loyalty Level'] = 'None'
                    
                    # Format Point Balance as currency (remove $ if present, ensure numeric format)
                    point_balance = filtered_df['Reward Points ($) Balance'].str.replace('$', '').str.replace(',', '')
                    formatted_df['Point Balance'] = point_balance
                    
                    formatted_df['Referral Source'] = filtered_df['Customer Source']
                    
                    # Columns 17-30
                    formatted_df['Created In Store'] = 'Y'
                    formatted_df['Doctor'] = 'N/A'
                    formatted_df['Doctor License'] = 'N/A'
                    formatted_df['Primary Document Type'] = "Driver's License"
                    formatted_df['Primary Document Number'] = filtered_df['Customer Drivers License']
                    formatted_df['Expiration Date'] = filtered_df['Customer Drivers License Expiration Date']
                    
                    # Medical Document Type: "MMID" if Medical Id is not empty, else "None"
                    formatted_df['Medical Document Type'] = filtered_df['Medical Id'].apply(
                        lambda x: 'MMID' if x.strip() != '' else 'None'
                    )
                    
                    # Medical Document Number: value from Medical Id, or "None" if empty
                    formatted_df['Medical Document Number'] = filtered_df['Medical Id'].apply(
                        lambda x: x if x.strip() != '' else 'None'
                    )
                    
                    formatted_df['Medical Document Expiration Date'] = filtered_df['Customer Medical Id Expiration Date']
                    formatted_df['Medical Document Renewal Rate'] = ''
                    formatted_df['Medical Document Issue Date'] = ''
                    formatted_df['Image URL'] = ''
                    
                    # Notes: up to 500 characters from Customer Profile Notes
                    formatted_df['Notes'] = filtered_df['Customer Profile Notes'].apply(
                        lambda x: x[:500] if len(x) > 500 else x
                    )
                    
                    formatted_df['Banned'] = filtered_df['Banned']
                    
                    # Store in session state
                    st.session_state.filtered_df = formatted_df
                    st.session_state.excluded_df = excluded_df
                    
                    st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error reading CSV file: {str(e)}")

# Display results if filtering has been done
if st.session_state.filtered_df is not None:
    filtered_df = st.session_state.filtered_df
    excluded_df = st.session_state.excluded_df
    original_df = st.session_state.original_df
    
    # Statistics
    st.success("✅ Filter Complete!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", len(original_df))
    with col2:
        st.metric("Rows Kept", len(filtered_df))
    with col3:
        st.metric("Rows Excluded", len(excluded_df))
    
    # Preview filtered data
    with st.expander("📊 Preview Filtered Data (first 10 rows)", expanded=True):
        st.dataframe(filtered_df.head(10))
    
    # Preview excluded data
    if len(excluded_df) > 0:
        with st.expander(f"🚫 Preview Excluded Data ({len(excluded_df)} rows)"):
            st.dataframe(excluded_df.head(10))
    
    # Download buttons
    st.markdown("### 📥 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Convert filtered data to CSV
        csv_filtered = filtered_df.to_csv(index=False)
        st.download_button(
            label=f"⬇️ Download Filtered Data ({len(filtered_df)} rows)",
            data=csv_filtered,
            file_name="filtered_output.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        if len(excluded_df) > 0:
            # Convert excluded data to CSV
            csv_excluded = excluded_df.to_csv(index=False)
            st.download_button(
                label=f"⬇️ Download Excluded Rows ({len(excluded_df)} rows)",
                data=csv_excluded,
                file_name="excluded_rows.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # Reset button
    if st.button("🔄 Reset & Upload New File", use_container_width=True):
        st.session_state.filtered_df = None
        st.session_state.excluded_df = None
        st.session_state.original_df = None
        st.rerun()

# Footer with filter criteria
st.markdown("---")
st.markdown("### 📋 Filter Criteria")
st.info("""
- Removes rows with "Canceled", "Cancelled", "Test", "Testing", or "Customer" in First/Last Name
- Removes rows with "N/A" or empty Customer Drivers License
- Case-insensitive matching for all text filters
""")
