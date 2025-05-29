# dashboard.py (Minimal Tabs Test - Step 2: Re-enable API call for columns)
import streamlit as st
import requests # Now needed again
import pandas as pd # Needed for type hints and if get_column_data_from_api processes it
from typing import List, Dict, Any, Optional 
# import traceback # Keep for later if needed

# --- Configuration ---
FASTAPI_BASE_URL = "http://localhost:8000/api" 

st.set_page_config(layout="wide", page_title="Data Analysis Dashboard")
st.title("📊 Data Analysis Dashboard - Column Fetch Test")

# --- Cached Function to Fetch Column Names (RE-ENABLED) ---
@st.cache_data(ttl=600) 
def get_column_data_from_api() -> Optional[Dict[str, List[str]]]:
    """Fetches all, categorical, and numerical column names from the API."""
    columns_endpoint = f"{FASTAPI_BASE_URL}/data/columns"
    st.write("DEBUG: Attempting to call get_column_data_from_api()...") # For UI debug
    try:
        response = requests.get(columns_endpoint)
        response.raise_for_status() 
        data = response.json()
        st.write("DEBUG: API call for columns successful.") # For UI debug
        print(f"DEBUG dashboard.py: get_column_data_from_api returned: {data}") # For terminal
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: Could not fetch column data. Is the backend server running? Details: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching column data: {e}")
        return None

# --- Initialize Column Lists (USING ACTUAL API CALL NOW) ---
column_data = get_column_data_from_api() # Re-enabled API call
all_columns: List[str] = []
numerical_cols: List[str] = []
categorical_cols: List[str] = []
default_fallback_cols = ["fallback_A", "fallback_B", "fallback_C"] 

if column_data:
    all_columns = column_data.get("all_columns", [])
    numerical_cols = column_data.get("numerical_columns", [])
    categorical_cols = column_data.get("categorical_columns", [])
    if not all_columns: 
        st.warning("Column data from API was empty. Using fallback names.")
        # Simplified fallback logic if primary lists are empty from API response
        all_columns = default_fallback_cols
        numerical_cols = [default_fallback_cols[0]] if default_fallback_cols else []
        categorical_cols = [default_fallback_cols[1]] if len(default_fallback_cols) > 1 else []
else: 
    st.warning("API for columns failed or returned None. Using fallback column names.")
    all_columns = default_fallback_cols
    numerical_cols = [default_fallback_cols[0]] if default_fallback_cols else []
    categorical_cols = [default_fallback_cols[1]] if len(default_fallback_cols) > 1 else []

st.write(f"DEBUG: Initialized `all_columns`: {all_columns[:5]}...") # UI Debug

# --- Sidebar Title ---
st.sidebar.title("Controls Area") 

# --- Create Tabs ---
tab_plots, tab_descriptive_stats, tab_data_view = st.tabs([
    "📊 Plot Dashboard", 
    "🔢 Descriptive Statistics", 
    "📄 View/Filter Data"
])

# --- Tab 1: Plot Dashboard (MINIMAL CONTENT) ---
with tab_plots:
    st.header("Plot Dashboard")
    st.write("Plot tab content placeholder.")
    # ALL controls and API calls for plots are still COMMENTED OUT / REMOVED

# --- Tab 2: Descriptive Statistics (MINIMAL CONTENT + TEST BUTTON) ---
with tab_descriptive_stats:
    st.header("Descriptive Statistics")
    st.write("This is the Descriptive Statistics Tab.")
    st.write("Testing if it stays active after button click with API call for columns active.")

    if st.button("Test Button in Descriptive Tab", key="minimal_test_btn_desc_tab_v3"): # New key for fresh state
        st.write("Test button in Descriptive Tab was clicked!")
        st.success("Button action completed. Did the tab stay active?")

    # ALL other controls (sidebar expander, multiselects) and API calls for stats are still COMMENTED OUT

# --- Tab 3: View/Filter Data (MINIMAL CONTENT) ---
with tab_data_view:
    st.header("View and Filter Data Subset")
    st.write("Data View tab content placeholder.")
    # ALL controls and API calls for data view are still COMMENTED OUT