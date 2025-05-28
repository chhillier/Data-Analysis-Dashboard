# dashboard.py
import streamlit as st
import requests
import pandas as pd 
from typing import List, Dict, Any, Optional # For type hints

# --- Configuration ---
FASTAPI_BASE_URL = "http://localhost:8000/api" # Ensure this matches your FastAPI server

st.set_page_config(layout="wide", page_title="Data Analysis Dashboard")
st.title("📊 Data Analysis Dashboard")

# --- Cached Function to Fetch Column Names ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def get_column_data_from_api() -> Optional[Dict[str, List[str]]]:
    """Fetches all, categorical, and numerical column names from the API."""
    columns_endpoint = f"{FASTAPI_BASE_URL}/data/columns"
    try:
        response = requests.get(columns_endpoint)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        # Use st.sidebar.error if you want errors to appear there when sidebar is active
        st.error(f"API Connection Error: Could not fetch column data. Is the backend server running? Details: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching column data: {e}")
        return None

# --- Initialize Column Lists ---
column_data = get_column_data_from_api()
all_columns: List[str] = []
numerical_cols: List[str] = []
categorical_cols: List[str] = []
# Provide more robust fallbacks if API is down during initial load
default_fallback_cols = ["column_A", "column_B", "column_C"] # Generic fallback

if column_data:
    all_columns = column_data.get("all_columns", [])
    numerical_cols = column_data.get("numerical_columns", [])
    categorical_cols = column_data.get("categorical_columns", [])
    if not all_columns: # If API returned empty lists
        st.warning("Column data from API was empty. Using fallback names for selectors.")
        all_columns = numerical_cols + [col for col in categorical_cols if col not in numerical_cols]
        if not all_columns: all_columns = default_fallback_cols
        if not numerical_cols: numerical_cols = default_fallback_cols
        if not categorical_cols: categorical_cols = default_fallback_cols

else: # column_data is None because API call failed
    st.warning("Using fallback column names as API for columns was not reachable or returned an error.")
    all_columns = default_fallback_cols
    numerical_cols = default_fallback_cols
    categorical_cols = default_fallback_cols


# --- Create Tabs ---
# Each tab can have its own set of controls, often placed in the sidebar.
# We can make the sidebar content dynamic based on the selected tab if needed,
# or have a common sidebar section and tab-specific main content.
# For now, let's make a general sidebar for controls.

st.sidebar.title("Controls")

tab_plots, tab_descriptive_stats, tab_data_view = st.tabs([
    "📊 Plot Dashboard", 
    "🔢 Descriptive Statistics", 
    "📄 View/Filter Data"
])


# --- Tab 1: Plot Dashboard ---
with tab_plots:
    st.header("Static Plot Dashboard")
    
    with st.sidebar.expander("Plot Dashboard Controls", expanded=True):
        st.subheader("Column Selection for Plots")
        plot_include_cols = st.multiselect("Include these columns for plots:", all_columns, default=None, key="plot_include")
        plot_exclude_cols = st.multiselect("Exclude these columns for plots:", all_columns, default=None, key="plot_exclude")

        if st.button("Generate Dashboard Plot", key="gen_dashboard_plot_tab"):
            endpoint_url = f"{FASTAPI_BASE_URL}/plots/dashboard"
            
            # Example plot configurations (can be made dynamic later)
            # Ensure columns used here are valid after any include/exclude from DataManager's post-processing
            current_plot_configurations = [
                {'type': 'histogram', 'params': {'col_name': 'carat', 'bins': 30, 'kde': True, 'color': 'skyblue'}},
                {'type': 'kde', 'params': {'col_name': 'price', 'hue_col': 'cut', 'fill': True, 'alpha': 0.6}},
                {'type': 'scatter', 'params': {'col_name_x': 'carat', 'col_name_y': 'price', 'hue_col': 'clarity', 'alpha': 0.4, 's': 20}},
                {'type': 'bar_chart', 'params': {'x_col': 'color', 'y_col': 'price', 'hue_col': 'cut', 'estimator': 'median', 'palette': 'viridis'}},
                {'type': 'count_plot', 'params': {'x_col': 'clarity', 'hue_col': 'cut', 'dodge': True}},
                {'type': 'crosstab_heatmap', 'params': {'index_names_ct': ['cut'], 'column_names_ct': ['color'], 'annot': True, 'fmt': '.0f'}}
            ]
            
            query_params_plots = {}
            if plot_include_cols: query_params_plots["include_columns"] = plot_include_cols
            if plot_exclude_cols: query_params_plots["exclude_columns"] = plot_exclude_cols
            
            st.info(f"Requesting dashboard plot from: {endpoint_url} with query_params: {query_params_plots}")
            # st.json({"plot_configurations_payload": current_plot_configurations}) # For debugging request

            try:
                with st.spinner("Generating dashboard plot... please wait."):
                    response = requests.post(endpoint_url, json=current_plot_configurations, params=query_params_plots) 
                response.raise_for_status()
                st.image(response.content, caption="Generated Dashboard Plot", use_container_width=True)
                st.success("Dashboard plot generated successfully!")
            except requests.exceptions.HTTPError as e:
                st.error(f"API Error (Dashboard Plot): {e.response.status_code}")
                try: st.json(e.response.json())
                except: st.text_area("Raw error response:", e.response.text, height=200)
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error to API: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

    with st.sidebar.expander("Individual Displot Controls", expanded=False):
        selected_col_displot = st.selectbox(
            "Select column for Displot:", numerical_cols,
            index=numerical_cols.index("price") if "price" in numerical_cols else 0,
            key="displot_col_select_tab"
        )
        selected_kind_displot = st.selectbox("Select Displot kind:", ["hist", "kde", "ecdf"], index=0, key="displot_kind_select_tab")
        selected_hue_displot = st.selectbox("Select Hue column for Displot (optional):", [None] + categorical_cols, index=0, key="displot_hue_select_tab")

        # Use plot_include_cols/plot_exclude_cols also for individual displot for consistency here
        # Or add separate selectors for displot if needed

        if st.button("Generate Displot", key="gen_displot_tab"):
            displot_endpoint_url = f"{FASTAPI_BASE_URL}/plots/displot"
            api_params = {"col_name": selected_col_displot, "kind": selected_kind_displot}
            if selected_hue_displot: api_params["hue_col"] = selected_hue_displot
            if plot_include_cols: api_params["include_columns"] = plot_include_cols
            if plot_exclude_cols: api_params["exclude_columns"] = plot_exclude_cols
            
            st.info(f"Requesting displot from: {displot_endpoint_url} with params: {api_params}")
            try:
                with st.spinner("Generating displot..."):
                    response = requests.get(displot_endpoint_url, params=api_params)
                response.raise_for_status()
                st.image(response.content, caption=f"Displot of {selected_col_displot}", use_container_width=True)
                st.success("Displot generated successfully!")
            except requests.exceptions.HTTPError as e:
                st.error(f"API Error (Displot): {e.response.status_code}")
                try: st.json(e.response.json())
                except: st.text_area("Raw error response:", e.response.text, height=200)
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error to API: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")


# --- Tab 2: Descriptive Statistics ---
with tab_descriptive_stats:
    st.header("Descriptive Statistics")
    
    with st.sidebar.expander("Descriptive Statistics Controls", expanded=True):
        st.subheader("Column Selection for Statistics")
        desc_include_cols = st.multiselect("Include these columns for statistics:", all_columns, default=None, key="desc_include")
        desc_exclude_cols = st.multiselect("Exclude these columns for statistics:", all_columns, default=None, key="desc_exclude")

    # Prepare query parameters for include/exclude once for this tab's general use
    query_params_for_desc_tab = {}
    if desc_include_cols: query_params_for_desc_tab["include_columns"] = desc_include_cols
    if desc_exclude_cols: query_params_for_desc_tab["exclude_columns"] = desc_exclude_cols

    # --- Numerical Summary ---
    st.subheader("Numerical Summary")
    if st.button("Show Numerical Summary", key="btn_num_summary"):
        endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/numerical-summary"
        # Add precision if you want to control it from UI, e.g., current_q_params["precision"] = selected_precision
        try:
            with st.spinner("Fetching numerical summary..."):
                response = requests.get(endpoint_url, params=query_params_for_desc_tab) 
            response.raise_for_status()
            summary_data_split = response.json()
            if summary_data_split and summary_data_split.get('data') is not None:
                df_summary = pd.DataFrame(summary_data_split['data'], columns=summary_data_split['columns'], index=summary_data_split['index'])
                st.dataframe(df_summary)
                st.success("Numerical summary loaded.")
            else:
                st.warning("Numerical summary data is empty or not in expected format.")
                st.json(summary_data_split)
        except requests.exceptions.HTTPError as e:
            st.error(f"API Error (Numerical Summary): {e.response.status_code}")
            try: st.json(e.response.json())
            except: st.text_area("Raw error response:", e.response.text, height=200)
        except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
        except Exception as e: st.error(f"Error processing numerical summary: {e}")
            
    st.markdown("---")

    # --- Categorical Summary ---
    st.subheader("Categorical Summary")
    if st.button("Show Categorical Summary", key="btn_cat_summary"):
        endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/categorical-summary"
        try:
            with st.spinner("Fetching categorical summary..."):
                response = requests.get(endpoint_url, params=query_params_for_desc_tab)
            response.raise_for_status()
            summary_data_split = response.json()
            if summary_data_split and summary_data_split.get('data') is not None:
                df_summary = pd.DataFrame(summary_data_split['data'], columns=summary_data_split['columns'], index=summary_data_split['index'])
                st.dataframe(df_summary)
                st.success("Categorical summary loaded.")
            else:
                st.warning("Categorical summary data is empty or not in expected format.")
                st.json(summary_data_split)
        except requests.exceptions.HTTPError as e:
            st.error(f"API Error (Categorical Summary): {e.response.status_code}")
            try: st.json(e.response.json())
            except: st.text_area("Raw error response:", e.response.text, height=200)
        except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
        except Exception as e: st.error(f"Error processing categorical summary: {e}")

    st.markdown("---")

    # --- Unique Counts ---
    st.subheader("Unique Value Counts (for Categorical Columns)")
    if st.button("Show Unique Counts", key="btn_unique_counts"):
        endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/unique-counts"
        try:
            with st.spinner("Fetching unique counts..."):
                response = requests.get(endpoint_url, params=query_params_for_desc_tab)
            response.raise_for_status()
            unique_counts_data = response.json() # Expects {"counts": {"col1": count1, ...}}
            if unique_counts_data and "counts" in unique_counts_data:
                st.json(unique_counts_data["counts"]) # Display the counts dictionary
                st.success("Unique counts loaded.")
            else:
                st.warning("Unique counts data is empty or not in expected format.")
                st.json(unique_counts_data)
        except requests.exceptions.HTTPError as e:
            st.error(f"API Error (Unique Counts): {e.response.status_code}")
            try: st.json(e.response.json())
            except: st.text_area("Raw error response:", e.response.text, height=200)
        except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
        except Exception as e: st.error(f"Error processing unique counts: {e}")

    st.markdown("---")

    # --- Frequency Table ---
    st.subheader("Frequency Table")
    if categorical_cols:
        selected_col_freq = st.selectbox(
            "Select a column for frequency table:", categorical_cols, index=0, key="freq_table_col_select"
        )
        if st.button("Show Frequency Table", key="btn_freq_table"):
            endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/frequency-table"
            current_q_params = query_params_for_desc_tab.copy()
            current_q_params["column_name"] = selected_col_freq
            try:
                with st.spinner(f"Fetching frequency table for {selected_col_freq}..."):
                    response = requests.get(endpoint_url, params=current_q_params)
                response.raise_for_status()
                freq_data_split = response.json()
                if freq_data_split and freq_data_split.get('data') is not None:
                    df_freq = pd.DataFrame(freq_data_split['data'], columns=freq_data_split['columns'], index=freq_data_split['index'])
                    st.dataframe(df_freq)
                    st.success(f"Frequency table for '{selected_col_freq}' loaded.")
                else:
                    st.warning(f"Frequency table for '{selected_col_freq}' is empty or not in expected format.")
                    st.json(freq_data_split)
            except requests.exceptions.HTTPError as e:
                st.error(f"API Error (Frequency Table): {e.response.status_code}")
                try: st.json(e.response.json())
                except: st.text_area("Raw error response:", e.response.text, height=200)
            except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
            except Exception as e: st.error(f"Error processing frequency table: {e}")
    else:
        st.info("No categorical columns available (according to API) to generate a frequency table.")
    
    st.markdown("---")

    # --- Cross-Tabulations ---
    st.subheader("Cross-Tabulations")
    if len(categorical_cols) >= 1: # Need at least one for index, one for columns ideally
        index_name_crosstab = st.multiselect("Select index column(s) for Crosstab:", categorical_cols, key="crosstab_index")
        column_name_crosstab = st.multiselect("Select column(s) for Crosstab:", categorical_cols, key="crosstab_columns")
        
        crosstab_normalize = st.checkbox("Normalize Crosstab?", value=False, key="crosstab_normalize")
        crosstab_margins = st.checkbox("Show Crosstab Margins?", value=False, key="crosstab_margins")

        if st.button("Generate Cross-Tabulation", key="btn_crosstab"):
            if not index_name_crosstab or not column_name_crosstab:
                st.warning("Please select at least one index and one column for cross-tabulation.")
            else:
                endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/cross-tabs" # POST endpoint
                payload = {
                    "index_names": index_name_crosstab,
                    "column_names": column_name_crosstab,
                    "normalize": crosstab_normalize,
                    "margins": crosstab_margins
                }
                try:
                    with st.spinner("Generating cross-tabulation..."):
                        # include/exclude query params for shaping before crosstab
                        response = requests.post(endpoint_url, json=payload, params=query_params_for_desc_tab)
                    response.raise_for_status()
                    crosstab_data_split = response.json()
                    if crosstab_data_split and crosstab_data_split.get('data') is not None:
                        df_crosstab = pd.DataFrame(crosstab_data_split['data'], columns=crosstab_data_split['columns'], index=crosstab_data_split['index'])
                        st.dataframe(df_crosstab)
                        st.success("Cross-tabulation loaded.")
                    else:
                        st.warning("Cross-tabulation data is empty or not in expected format.")
                        st.json(crosstab_data_split)
                except requests.exceptions.HTTPError as e:
                    st.error(f"API Error (Crosstab): {e.response.status_code}")
                    try: st.json(e.response.json())
                    except: st.text_area("Raw error response:", e.response.text, height=200)
                except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
                except Exception as e: st.error(f"Error processing cross-tabulation: {e}")
    else:
        st.info("Not enough categorical columns available (according to API) for cross-tabulation.")

    st.markdown("---")

    # --- Dataset Shape and Info (already have include/exclude via query_params_for_desc_tab) ---
    st.subheader("Other Dataset Information")
    col1_info, col2_info = st.columns(2)
    with col1_info:
        if st.button("Show Dataset Shape", key="btn_shape"):
            endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/shape"
            try:
                with st.spinner("Fetching dataset shape..."):
                    response = requests.get(endpoint_url, params=query_params_for_desc_tab)
                response.raise_for_status()
                st.json(response.json())
                st.success("Dataset shape loaded.")
            except requests.exceptions.HTTPError as e: st.error(f"API Error (Shape): {e.response.status_code}"); st.json(e.response.json())
            except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
            except Exception as e: st.error(f"Error processing shape: {e}")
    with col2_info:
        if st.button("Show Dataset Info", key="btn_info"):
            endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/info"
            try:
                with st.spinner("Fetching dataset info..."):
                    response = requests.get(endpoint_url, params=query_params_for_desc_tab)
                response.raise_for_status()
                info_data = response.json()
                st.text_area("Dataset Info (df.info())", info_data.get("info_string", "No info available."), height=300)
                st.success("Dataset info loaded.")
            except requests.exceptions.HTTPError as e: st.error(f"API Error (Info): {e.response.status_code}"); st.json(e.response.json())
            except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
            except Exception as e: st.error(f"Error processing info: {e}")


# --- Tab 3: View/Filter Data ---
with tab_data_view:
    st.header("View and Filter Data Subset")
    
    with st.sidebar.expander("Data View & Filter Controls", expanded=True):
        st.subheader("Row Filters")
        filter_col_select = st.selectbox(
            "Filter by column:", [None] + all_columns, index=0, key="filter_col_select_view"
        )
        filter_value_input = None
        if filter_col_select:
            filter_value_input = st.text_input(
                f"Enter value to filter for in '{filter_col_select}':", key="filter_value_input_view"
            )

        st.subheader("Column Selection for View")
        view_include_cols = st.multiselect("Include these columns in view:", all_columns, default=all_columns, key="view_include")
        view_exclude_cols = st.multiselect("Exclude these columns from view:", all_columns, default=None, key="view_exclude")

        if st.button("Show Filtered/Shaped Data", key="btn_show_filtered_data"): # Changed button label for clarity
            endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/filter" # POST endpoint
            
            filter_payload = {"cols": [], "values": []}
            if filter_col_select and filter_value_input: # Ensure both are provided
                # For API, best to send lists even for single.
                # Type conversion for filter_value_input would ideally happen based on column dtype.
                # For now, sending as string.
                filter_payload["cols"] = [filter_col_select]
                filter_payload["values"] = [filter_value_input] 
            
            query_params_view = {}
            if view_include_cols: query_params_view["include_columns"] = view_include_cols
            if view_exclude_cols: query_params_view["exclude_columns"] = view_exclude_cols

            st.info(f"Requesting filtered data from: {endpoint_url}")
            # st.json({"row_filter_payload": filter_payload, "column_shape_query_params": query_params_view}) # For debugging

            try:
                with st.spinner("Fetching filtered data..."):
                    # Row filter criteria go in the JSON body (payload)
                    # Column shaping (include/exclude) go as query parameters
                    response = requests.post(endpoint_url, json=filter_payload, params=query_params_view)
                response.raise_for_status()
                filtered_data_records = response.json() 

                if filtered_data_records and "records" in filtered_data_records:
                    df_filtered = pd.DataFrame.from_records(filtered_data_records["records"])
                    st.dataframe(df_filtered)
                    st.success(f"Filtered data loaded. Displaying {len(df_filtered)} rows.")
                    if df_filtered.empty and (filter_payload["cols"] or query_params_view):
                        st.info("The current filter and/or column selection resulted in no data.")
                else:
                    st.warning("Filtered data is empty or not in expected 'records' format.")
                    st.json(filtered_data_records) # Show what was received
            except requests.exceptions.HTTPError as e:
                st.error(f"API Error (Filtered Data): {e.response.status_code}")
                try: st.json(e.response.json())
                except: st.text_area("Raw error response:", e.response.text, height=200)
            except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
            except Exception as e: st.error(f"Error processing filtered data: {e}")