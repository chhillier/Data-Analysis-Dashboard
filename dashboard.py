# dashboard.py
import streamlit as st
import requests
import pandas as pd 
from typing import List, Dict, Any, Optional 
import traceback # For more detailed error printing in Streamlit console

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
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
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
default_fallback_cols = ["column_A", "column_B", "column_C"] 

if column_data:
    all_columns = column_data.get("all_columns", [])
    numerical_cols = column_data.get("numerical_columns", [])
    categorical_cols = column_data.get("categorical_columns", [])
    if not all_columns: 
        st.warning("Column data from API was empty. Using fallback names for selectors.")
        all_columns = numerical_cols + [col for col in categorical_cols if col not in numerical_cols]
        if not all_columns: all_columns = default_fallback_cols
        if not numerical_cols: numerical_cols = default_fallback_cols
        if not categorical_cols: categorical_cols = default_fallback_cols
else: 
    st.warning("Using fallback column names as API for columns was not reachable or returned an error.")
    all_columns = default_fallback_cols
    numerical_cols = default_fallback_cols
    categorical_cols = default_fallback_cols

# --- Create Tabs ---
st.sidebar.title("Controls")
tab_plots, tab_descriptive_stats, tab_data_view = st.tabs([
    "📊 Plot Dashboard", 
    "🔢 Descriptive Statistics", 
    "📄 View/Filter Data"
])
# In dashboard.py


# ... (FASTAPI_BASE_URL, get_column_data_from_api, column list initializations) ...

def display_df_from_api_split_response(
    response_data_split: Dict[str, Any], 
    success_message: str = "Data loaded.", 
    index_level_names: Optional[List[str]] = None
):
    # This function assumes response_data_split is already the parsed JSON dict from response.json()
    # Commenting out the UI debug for cleaner default display, but you can re-enable if needed.
    # st.write("DEBUG UI: Raw JSON response for table (passed to display_df_from_api_split_response):")
    # st.json(response_data_split)
    
    print("\n--- DEBUG dashboard.py: display_df_from_api_split_response ---") 
    print(f"Received response_data_split type: {type(response_data_split)}")
    
    index_from_json = response_data_split.get('index', [])
    columns_from_json = response_data_split.get('columns', [])
    data_from_json = response_data_split.get('data', [])

    print(f"Index from JSON type: {type(index_from_json)}, Length: {len(index_from_json)}")
    if index_from_json: print(f"  Index example (first 3): {index_from_json[:3]}")
    print(f"Columns from JSON type: {type(columns_from_json)}, Length: {len(columns_from_json)}")
    if columns_from_json: print(f"  Columns example (first 5): {columns_from_json[:5]}")
    print(f"Data from JSON type: {type(data_from_json)}, Num_rows_in_data: {len(data_from_json)}")
    if data_from_json and isinstance(data_from_json, list) and len(data_from_json) > 0 and isinstance(data_from_json[0], list) :
        print(f"  Num_cols_in_first_data_row: {len(data_from_json[0]) if data_from_json[0] else 'N/A'}")
    elif data_from_json:
        print(f"  First data element type: {type(data_from_json[0])}")
    print(f"Provided index_level_names for reconstruction: {index_level_names}")
    print("--------------------------------------------------------------\n")

    if (response_data_split and 
        data_from_json is not None and 
        columns_from_json is not None and
        index_from_json is not None):
        
        try:
            reconstructed_index = None
            if index_from_json: 
                processed_index_tuples = [tuple(item) if isinstance(item, list) else item for item in index_from_json]
                if processed_index_tuples and isinstance(processed_index_tuples[0], tuple): 
                    print(f"DEBUG: Reconstructing as MultiIndex. Names: {index_level_names}. Number of tuples: {len(processed_index_tuples)}")
                    reconstructed_index = pd.MultiIndex.from_tuples(processed_index_tuples, names=index_level_names)
                else: 
                    idx_name_for_single = None
                    if index_level_names and isinstance(index_level_names, list) and len(index_level_names) == 1:
                        idx_name_for_single = index_level_names[0]
                    elif isinstance(index_level_names, str): 
                        idx_name_for_single = index_level_names
                    print(f"DEBUG: Reconstructing as Single Index. Name: {idx_name_for_single}. Values example: {processed_index_tuples[:3]}")
                    reconstructed_index = pd.Index(processed_index_tuples, name=idx_name_for_single)
            elif not data_from_json : 
                print("DEBUG: Both index and data from JSON are empty. Creating empty index for empty DataFrame.")
                reconstructed_index = pd.Index([])
            
            print(f"DEBUG: Attempting to create DataFrame with Data rows: {len(data_from_json)}, "
                  f"Index object: {type(reconstructed_index).__name__} with {len(reconstructed_index) if reconstructed_index is not None else 'N/A'} items, "
                  f"Column items: {len(columns_from_json)}")
            
            df_display = pd.DataFrame(
                data=data_from_json, 
                index=reconstructed_index, 
                columns=columns_from_json
            )
            
            print(f"DEBUG: DataFrame created in Streamlit. Shape: {df_display.shape}")
            # print(f"DEBUG: DataFrame dtypes BEFORE astype(str) for categoricals: \n{df_display.dtypes}")

            # --- EXPLICITLY CONVERT IDENTIFIED CATEGORICALS TO STRING FOR ARROW ---
            # 'categorical_cols' is the list fetched from your API (and made globally available in dashboard.py)
            # which contains names of columns your backend identified as 'category', 'object', or 'int'
            # that might be best treated as strings for display to avoid Arrow type inference issues.
            
            # Ensure categorical_cols is accessible (it should be a global in dashboard.py)
            cols_to_stringify_for_display = [col for col in categorical_cols if col in df_display.columns]
            
            if cols_to_stringify_for_display:
                print(f"DEBUG: Will attempt to convert these columns to string for st.dataframe: {cols_to_stringify_for_display}")
                for col_name_to_str in cols_to_stringify_for_display:
                    try:
                        df_display[col_name_to_str] = df_display[col_name_to_str].astype(str)
                        # print(f"DEBUG: Column '{col_name_to_str}' successfully converted to string dtype for display.")
                    except Exception as e_astype:
                        print(f"DEBUG: Could not convert column '{col_name_to_str}' to string: {e_astype}")
                        # st.warning(f"Note: Could not ensure string type for display of column '{col_name_to_str}'.")
            
            # print(f"DEBUG: DataFrame dtypes AFTER astype(str) for categoricals: \n{df_display.dtypes}")
            # --- END OF TYPE CONVERSION SECTION ---

            st.dataframe(df_display) # Display the DataFrame with corrected types
            st.success(success_message)

        except ValueError as ve: 
            st.error(f"Pandas Error creating/processing DataFrame from API response: {ve}")
            print(f"--- PANDAS DataFrame CREATION/PROCESSING ValueError (Streamlit Console) ---")
            traceback.print_exc()
            print(f"-------------------------------------------------------------------------")
        except Exception as ex_df_create: 
            st.error(f"Unexpected error creating/processing DataFrame: {ex_df_create}")
            print(f"--- UNEXPECTED DataFrame CREATION/PROCESSING Error (Streamlit Console) ---")
            traceback.print_exc()
            print(f"----------------------------------------------------------------------")
    else:
        st.warning("Data received from API for table is incomplete, not in expected 'split' format, or data array is None.")


# --- Tab 1: Plot Dashboard ---
with tab_plots:
    st.header("Static Plot Dashboard")

    with st.sidebar.expander("Plot Dashboard Controls", expanded=True):
        st.subheader("Column Selection for Plots")
        plot_include_cols = st.multiselect("Include columns for plots:", all_columns, default=None, key="plot_include")
        plot_exclude_cols = st.multiselect("Exclude columns for plots:", all_columns, default=None, key="plot_exclude")

        if st.button("Generate Dashboard Plot", key="gen_dashboard_plot_tab"):
            endpoint_url = f"{FASTAPI_BASE_URL}/plots/dashboard"
            current_plot_configurations = [
                {'type': 'histogram', 'params': {'col_name': 'carat', 'bins': 30, 'kde': True, 'color': 'skyblue', 'edgecolor': 'black', 'linewidth': 1}},
                {'type': 'kde', 'params': {'col_name': 'price', 'hue_col': 'cut', 'fill': True, 'alpha': 0.7, 'linewidth': 1.5, 'palette': 'viridis'}},
                {'type': 'scatter', 'params': {'col_name_x': 'carat', 'col_name_y': 'price', 'hue_col': 'clarity', 'alpha': 0.4, 's': 20, 'edgecolor': 'w', 'linewidth': 0.5}},
                {'type': 'bar_chart', 'params': {'x_col': 'color', 'y_col': 'price', 'hue_col': 'cut', 'estimator': 'median', 'palette': 'viridis', 'saturation': 0.75, 'errorbar': ('ci', 95)}},
                {'type': 'count_plot', 'params': {'x_col': 'clarity', 'hue_col': 'cut', 'dodge': True, 'palette': 'coolwarm'}},
                {'type': 'crosstab_heatmap', 'params': {'index_names_ct': ['cut'], 'column_names_ct': ['color'], 'annot': True, 'fmt': '.0f', 'cmap': 'YlGnBu', 'cbar': False, 'heatmap_linewidths': 0.5}}
            ]
            query_params_plots = {}
            if plot_include_cols: query_params_plots["include_columns"] = plot_include_cols
            if plot_exclude_cols: query_params_plots["exclude_columns"] = plot_exclude_cols
            st.info(f"Requesting dashboard plot from: {endpoint_url} with query_params: {query_params_plots}")
            try:
                with st.spinner("Generating dashboard plot... please wait."):
                    response = requests.post(endpoint_url, json=current_plot_configurations, params=query_params_plots) 
                response.raise_for_status()
                st.image(response.content, caption="Generated Dashboard Plot", use_container_width=True)
                st.success("Dashboard plot generated successfully!")
            except requests.exceptions.HTTPError as e:
                st.error(f"API Error (Dashboard Plot): Status {e.response.status_code}")
                try: st.json(e.response.json())
                except: st.text_area("Raw error response:", e.response.text, height=200)
            except requests.exceptions.RequestException as e: st.error(f"Connection error to API: {e}")
            except Exception as e: st.error(f"An unexpected error occurred: {e}")

    with st.sidebar.expander("Individual Displot Controls", expanded=False):
        displot_col_index = 0
        if "price" in numerical_cols: displot_col_index = numerical_cols.index("price")
        elif numerical_cols: displot_col_index = 0
        selected_col_displot = st.selectbox("Select column for Displot:", numerical_cols, index=displot_col_index, key="displot_col_select_tab")
        selected_kind_displot = st.selectbox("Select Displot kind:", ["hist", "kde", "ecdf"], index=0, key="displot_kind_select_tab")
        selected_hue_displot = st.selectbox("Select Hue column for Displot (optional):", [None] + categorical_cols, index=0, key="displot_hue_select_tab")

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
                st.error(f"API Error (Displot): Status {e.response.status_code}")
                try: st.json(e.response.json())
                except: st.text_area("Raw error response:", e.response.text, height=200)
            except requests.exceptions.RequestException as e: st.error(f"Connection error to API: {e}")
            except Exception as e: st.error(f"An unexpected error occurred: {e}")


# --- Tab 2: Descriptive Statistics ---
with tab_descriptive_stats:
    st.header("Descriptive Statistics")
    st.write("This is a Descriptive Statistics Tab - testing if it stays active")
    """"""
    # with st.sidebar.expander("Descriptive Statistics Controls", expanded=True):
    #     st.subheader("Column Selection for Statistics")
    
    #     desc_include_cols = st.multiselect("Include columns for statistics:", all_columns, default=None, key="desc_include")
    #     desc_exclude_cols = st.multiselect("Exclude columns for statistics:", all_columns, default=None, key="desc_exclude")

    # query_params_for_desc_tab = {}
    # if desc_include_cols: query_params_for_desc_tab["include_columns"] = desc_include_cols
    # if desc_exclude_cols: query_params_for_desc_tab["exclude_columns"] = desc_exclude_cols
    """"""
    # st.subheader("Numerical Summary")
    # if st.button("Show Numerical Summary", key="btn_num_summary"):
    #     endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/numerical-summary"
    #     try:
    #         with st.spinner("Fetching numerical summary..."):
    #             response = requests.get(endpoint_url, params=query_params_for_desc_tab) 
    #         response.raise_for_status() 
    #         display_df_from_api_split_response(response.json(), "Numerical summary loaded.")
    #     except requests.exceptions.HTTPError as e: st.error(f"API Error (Numerical Summary): Status {e.response.status_code}"); st.json(e.response.json())
    #     except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
    #     except Exception as e: st.error(f"Error processing numerical summary: {e}")
    # In dashboard.py, within tab_descriptive_stats:

    st.subheader("Numerical Summary")
    if st.button("Show Numerical Summary", key="btn_num_summary"): # Ensure this key is unique if you had another temp one
        st.write("Button for Numerical Summary was clicked!")
        st.success("Test: Action registered, no API call made.")
        # --- Temporarily comment out the entire API call and display logic ---
        """
        endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/numerical-summary"
        try:
            with st.spinner("Fetching numerical summary..."):
                # query_params_for_desc_tab should be defined if the sidebar expander is active
                # If sidebar expander is still commented out, params will be empty
                response = requests.get(endpoint_url, params=query_params_for_desc_tab) 
            response.raise_for_status() 
            display_df_from_api_split_response(response.json(), "Numerical summary loaded.")
        except requests.exceptions.HTTPError as e: 
            st.error(f"API Error (Numerical Summary): Status {e.response.status_code}")
            # Try to display JSON error from FastAPI if possible
            try:
                st.json(e.response.json())
            except: # If response isn't JSON or other error
                st.text_area("Raw error response:", e.response.text, height=100)
        except requests.exceptions.RequestException as e: 
            st.error(f"API Connection Error: {e}")
        except Exception as e: 
            st.error(f"Error processing numerical summary: {e}")
            # For detailed debugging in Streamlit's console:
            # import traceback
            # print("--- Error in Numerical Summary (Streamlit Console) ---")
            # traceback.print_exc()
            # print("------------------------------------------------------")
        """
            
    st.markdown("---")
    # ... (rest of the tab, ideally still mostly commented out for this test) ...
            
    # st.markdown("---")
    # st.subheader("Categorical Summary")
    # if st.button("Show Categorical Summary", key="btn_cat_summary"):
    #     endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/categorical-summary"
    #     try:
    #         with st.spinner("Fetching categorical summary..."):
    #             response = requests.get(endpoint_url, params=query_params_for_desc_tab)
    #         response.raise_for_status()
    #         display_df_from_api_split_response(response.json(), "Categorical summary loaded.")
    #     except requests.exceptions.HTTPError as e: st.error(f"API Error (Categorical Summary): Status {e.response.status_code}"); st.json(e.response.json())
    #     except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
    #     except Exception as e: st.error(f"Error processing categorical summary: {e}")

    # st.markdown("---")
    # st.subheader("Unique Value Counts")
    # if st.button("Show Unique Counts", key="btn_unique_counts"):
    #     endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/unique-counts"
    #     try:
    #         with st.spinner("Fetching unique counts..."):
    #             response = requests.get(endpoint_url, params=query_params_for_desc_tab)
    #         response.raise_for_status()
    #         unique_counts_data = response.json() 
    #         if unique_counts_data and "counts" in unique_counts_data:
    #             st.json(unique_counts_data["counts"])
    #             st.success("Unique counts loaded.")
    #         else: st.warning("Unique counts data not in expected format."); st.json(unique_counts_data)
    #     except requests.exceptions.HTTPError as e: st.error(f"API Error (Unique Counts): Status {e.response.status_code}"); st.json(e.response.json())
    #     except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
    #     except Exception as e: st.error(f"Error processing unique counts: {e}")

    # st.markdown("---")
    # st.subheader("Frequency Table")
    # if categorical_cols:
    #     freq_col_index = 0
    #     if "cut" in categorical_cols: freq_col_index = categorical_cols.index("cut")
    #     elif categorical_cols: freq_col_index = 0

    #     selected_col_freq = st.selectbox("Select column for frequency table:", categorical_cols, index=freq_col_index, key="freq_table_col_select")
    #     if st.button("Show Frequency Table", key="btn_freq_table"):
    #         endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/frequency-table"
    #         current_q_params = query_params_for_desc_tab.copy()
    #         current_q_params["column_name"] = selected_col_freq
    #         try:
    #             with st.spinner(f"Fetching frequency table for {selected_col_freq}..."):
    #                 response = requests.get(endpoint_url, params=current_q_params)
    #             response.raise_for_status()
    #             display_df_from_api_split_response(response.json(), f"Frequency table for '{selected_col_freq}' loaded.", index_level_names=[selected_col_freq])
    #         except requests.exceptions.HTTPError as e: st.error(f"API Error (Frequency Table): Status {e.response.status_code}"); st.json(e.response.json())
    #         except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
    #         except Exception as e: st.error(f"Error processing frequency table: {e}")
    # else:
    #     st.info("No categorical columns available for frequency table.")
    
    # st.markdown("---")
    # st.subheader("Cross-Tabulations")
    # if len(categorical_cols) >= 1: # Check if there are enough columns for default selection
    #     # Make default selections safer
    #     default_index_ct = [categorical_cols[0]] if categorical_cols else []
    #     default_cols_ct = [categorical_cols[1]] if len(categorical_cols) > 1 else ([categorical_cols[0]] if categorical_cols else [])
        
    #     index_name_crosstab_select = st.multiselect("Select index column(s) for Crosstab:", categorical_cols, default=default_index_ct, key="crosstab_index")
    #     column_name_crosstab_select = st.multiselect("Select column(s) for Crosstab:", categorical_cols, default=default_cols_ct, key="crosstab_columns")
        
    #     crosstab_normalize = st.checkbox("Normalize Crosstab?", value=False, key="crosstab_normalize")
    #     crosstab_margins = st.checkbox("Show Crosstab Margins?", value=False, key="crosstab_margins")

    #     if st.button("Generate Cross-Tabulation", key="btn_crosstab"):
    #         if not index_name_crosstab_select or not column_name_crosstab_select:
    #             st.warning("Please select at least one index AND one column for cross-tabulation.")
    #         else:
    #             endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/cross-tabs" 
    #             payload = {
    #                 "index_names": index_name_crosstab_select,
    #                 "column_names": column_name_crosstab_select, 
    #                 "normalize": crosstab_normalize,
    #                 "margins": crosstab_margins
    #             }
    #             #st.write("DEBUG UI: Sending payload for crosstab:")
    #             #st.json(payload)
    #             #st.write("DEBUG UI: Sending query_params for crosstab (column shaping):")
    #             #st.json(query_params_for_desc_tab)

    #             try:
    #                 with st.spinner("Generating cross-tabulation..."):
    #                     response = requests.post(endpoint_url, json=payload, params=query_params_for_desc_tab)
    #                 response.raise_for_status() 
    #                 display_df_from_api_split_response(response.json(), "Cross-tabulation loaded.", index_level_names=index_name_crosstab_select)
    #             except requests.exceptions.HTTPError as e: 
    #                 st.error(f"API Error (Crosstab): Status {e.response.status_code}")
    #                 try: st.json(e.response.json()) 
    #                 except: st.text_area("Raw error response:", e.response.text, height=200)
    #             except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
    #             except Exception as e: 
    #                 st.error(f"Error processing cross-tabulation: {e}")
    #                 print(f"--- Error processing cross-tabulation (Streamlit Console) ---")
    #                 traceback.print_exc()
    #                 print(f"-------------------------------------------------------------")
    # else:
    #     st.info("Not enough categorical columns for cross-tabulation.")

    # st.markdown("---")
    # st.subheader("Other Dataset Information")
    # col1_info, col2_info = st.columns(2)
    # with col1_info:
    #     if st.button("Show Dataset Shape", key="btn_shape"):
    #         endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/shape"
    #         try:
    #             with st.spinner("Fetching dataset shape..."):
    #                 response = requests.get(endpoint_url, params=query_params_for_desc_tab)
    #             response.raise_for_status()
    #             st.json(response.json())
    #             st.success("Dataset shape loaded.")
    #         except requests.exceptions.HTTPError as e: st.error(f"API Error (Shape): Status {e.response.status_code}"); st.json(e.response.json())
    #         except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
    #         except Exception as e: st.error(f"Error processing shape: {e}")
    # with col2_info:
    #     if st.button("Show Dataset Info", key="btn_info"):
    #         endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/info"
    #         try:
    #             with st.spinner("Fetching dataset info..."):
    #                 response = requests.get(endpoint_url, params=query_params_for_desc_tab)
    #             response.raise_for_status()
    #             info_data = response.json()
    #             st.text_area("Dataset Info (df.info())", info_data.get("info_string", "No info available."), height=300)
    #             st.success("Dataset info loaded.")
    #         except requests.exceptions.HTTPError as e: st.error(f"API Error (Info): Status {e.response.status_code}"); st.json(e.response.json())
    #         except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
    #         except Exception as e: st.error(f"Error processing info: {e}")


# --- Tab 3: View/Filter Data ---
with tab_data_view:
    st.header("View and Filter Data Subset")
    
    with st.sidebar.expander("Data View & Filter Controls", expanded=True):
        st.subheader("Row Filters")
        filter_col_select = st.selectbox("Filter by column:", [None] + all_columns, index=0, key="filter_col_select_view")
        filter_value_input = "" 
        if filter_col_select:
            filter_value_input = st.text_input(f"Enter value to filter for in '{filter_col_select}':", key="filter_value_input_view")

        st.subheader("Column Selection for View")
        view_tab_include_cols_default = all_columns if all_columns else [] 
        view_tab_include_cols = st.multiselect("Include columns in view:", all_columns, default=view_tab_include_cols_default, key="view_tab_include")
        view_tab_exclude_cols = st.multiselect("Exclude columns from view:", all_columns, default=None, key="view_tab_exclude")

        if st.button("Show Filtered/Shaped Data", key="btn_show_filtered_data"):
            endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/filter" 
            
            filter_payload = {"cols": [], "values": []}
            if filter_col_select and filter_value_input.strip(): 
                filter_payload["cols"] = [filter_col_select]
                filter_payload["values"] = [filter_value_input] 
            
            query_params_view = {}
            if view_tab_include_cols: query_params_view["include_columns"] = view_tab_include_cols
            if view_tab_exclude_cols: query_params_view["exclude_columns"] = view_tab_exclude_cols

            st.info(f"Requesting filtered data. Payload: {filter_payload}, Query Params: {query_params_view}")
            try:
                with st.spinner("Fetching filtered data..."):
                    response = requests.post(endpoint_url, json=filter_payload, params=query_params_view)
                response.raise_for_status()
                filtered_data_api_response = response.json() 

                if filtered_data_api_response and "records" in filtered_data_api_response:
                    df_filtered = pd.DataFrame.from_records(filtered_data_api_response["records"])
                    st.dataframe(df_filtered)
                    st.success(f"Filtered data loaded. Displaying {len(df_filtered)} rows.")
                    if df_filtered.empty and (filter_payload["cols"] or query_params_view):
                        st.info("The current filter and/or column selection resulted in no data.")
                else:
                    st.warning("Filtered data is empty or not in expected 'records' format.")
                    st.json(filtered_data_api_response)
            except requests.exceptions.HTTPError as e:
                st.error(f"API Error (Filtered Data): Status {e.response.status_code}")
                try: st.json(e.response.json())
                except: st.text_area("Raw error response:", e.response.text, height=200)
            except requests.exceptions.RequestException as e: st.error(f"API Connection Error: {e}")
            except Exception as e: 
                st.error(f"Error processing filtered data: {e}")
                print("--- Error processing filtered data (Streamlit Console) ---")
                traceback.print_exc()
                print("----------------------------------------------------------")