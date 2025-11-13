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
        required_cols = ['First Name', 'Last Name', 'Customer Drivers License']
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
                            "canceled|cancelled|test|testing", 
                            case=False, 
                            na=False,
                            regex=True
                        ) &
                        ~df["Last Name"].str.contains(
                            "canceled|cancelled|test|testing", 
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
                    
                    # Store in session state
                    st.session_state.filtered_df = filtered_df
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
- Removes rows with "Canceled", "Cancelled", "Test", or "Testing" in First/Last Name
- Removes rows with "N/A" or empty Customer Drivers License
- Case-insensitive matching for all text filters
""")
