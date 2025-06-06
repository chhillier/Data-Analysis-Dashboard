# dashboard.py
import streamlit as st
import requests 
import pandas as pd 
from typing import List, Dict, Any, Optional, Union
import traceback

# --- Configuration ---
FASTAPI_BASE_URL = "http://localhost:8000/api" 

st.set_page_config(layout="wide", page_title="Data Analysis Dashboard")
st.title("📊 Data Analysis Dashboard")

# --- API Helper Functions ---
@st.cache_data(ttl=600) 
def get_column_data_from_api() -> Optional[Dict[str, List[str]]]:
    """Fetches column names from the API for the currently active dataset."""
    columns_endpoint = f"{FASTAPI_BASE_URL}/data/columns"
    try:
        response = requests.get(columns_endpoint)
        response.raise_for_status() 
        return response.json()
    except Exception as e:
        st.error(f"Connection Error fetching columns: {e}")
        return None

@st.cache_data(ttl=3600)
def get_available_datasets() -> List[str]:
    """Fetches the list of available dataset names from the API."""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/datasets")
        response.raise_for_status()
        data = response.json()
        return data.get("datasets", [])
    except Exception as e:
        st.error(f"Could not fetch dataset list from API: {e}")
        return []

def display_df_from_api_split_response(
    response_data_split: Dict[str, Any], 
    success_message: str = "Data loaded.", 
    index_level_names: Optional[List[str]] = None
):
    """Reconstructs and displays a DataFrame from a 'split' format JSON response."""
    try:
        index_from_json = response_data_split.get('index', [])
        columns_from_json = response_data_split.get('columns', [])
        data_from_json = response_data_split.get('data', [])
        
        reconstructed_index = None
        if index_from_json: 
            processed_index_tuples = [tuple(item) if isinstance(item, list) else item for item in index_from_json]
            if processed_index_tuples and isinstance(processed_index_tuples[0], tuple): 
                reconstructed_index = pd.MultiIndex.from_tuples(processed_index_tuples, names=index_level_names)
            else: 
                idx_name = index_level_names[0] if index_level_names and len(index_level_names) == 1 else None
                reconstructed_index = pd.Index(processed_index_tuples, name=idx_name)
        
        df_display = pd.DataFrame(data=data_from_json, index=reconstructed_index, columns=columns_from_json)
        st.dataframe(df_display)
        st.success(success_message)
    except Exception as e: 
        st.error(f"Error displaying DataFrame: {e}")

# --- Session State Initialization ---
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.active_dataset = "diamonds"
    
    st.session_state.show_numerical_summary = False
    st.session_state.show_categorical_summary = False
    st.session_state.show_unique_counts = False 
    st.session_state.show_frequency_table_section = False
    st.session_state.show_crosstab_section = False      
    st.session_state.show_dataset_shape = False
    st.session_state.show_dataset_info = False
    st.session_state.show_filtered_data_view = False
    st.rerun()

# --- Data-Dependent Initialization ---
column_data = get_column_data_from_api() 
if column_data:
    st.session_state.all_columns = column_data.get("all_columns", [])
    st.session_state.numerical_cols = column_data.get("numerical_columns", [])
    st.session_state.categorical_cols = column_data.get("categorical_columns", [])
else: 
    st.session_state.all_columns = []
    st.session_state.numerical_cols = []
    st.session_state.categorical_cols = []

all_columns: List[str] = st.session_state.get('all_columns', [])
numerical_cols: List[str] = st.session_state.get('numerical_cols', [])
categorical_cols: List[str] = st.session_state.get('categorical_cols', [])

# --- Main App UI ---
st.sidebar.title("Controls & Options")

st.markdown("### 1. Select a Dataset")
available_datasets = get_available_datasets()

if available_datasets:
    try:
        current_selection_index = available_datasets.index(st.session_state.active_dataset)
    except ValueError:
        current_selection_index = 0

    selected_dataset = st.selectbox(label="Choose a dataset to analyze:", options=available_datasets, index=current_selection_index, key="dataset_selector")

    if selected_dataset and (selected_dataset != st.session_state.active_dataset):
        with st.spinner(f"Loading '{selected_dataset}'..."):
            try:
                select_url = f"{FASTAPI_BASE_URL}/datasets/select/{selected_dataset}"
                response = requests.post(select_url)
                response.raise_for_status()
                
                new_active_dataset = selected_dataset
                
                protected_keys = ['app_initialized'] 
                for key in list(st.session_state.keys()):
                    if key not in protected_keys:
                        del st.session_state[key]
                
                st.session_state.active_dataset = new_active_dataset
                st.cache_data.clear()
                st.rerun()

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to switch dataset. API error: {e}")
else:
    st.warning("No datasets discovered. Please check the `datasets` folder and the backend API.")

st.markdown("---")

tab_plots, tab_descriptive_stats, tab_data_view = st.tabs([
    "📊 Plot Dashboard", 
    "🔢 Descriptive Statistics", 
    "📄 View/Filter Data"
])

with tab_plots:
    st.header("Plot Generation")
    with st.expander("Plot Controls", expanded=True):
        st.subheader("Column Selection for Plot")
        plot_tab_include_cols = st.multiselect("Include columns:", all_columns, default=None, key="plot_tab_include_main")
        plot_tab_exclude_cols = st.multiselect("Exclude columns:", all_columns, default=None, key="plot_tab_exclude_main")

        effective_cols_for_plot_ui = list(all_columns)
        if plot_tab_include_cols:
            effective_cols_for_plot_ui = [col for col in all_columns if col in plot_tab_include_cols]
        elif plot_tab_exclude_cols:
            effective_cols_for_plot_ui = [col for col in all_columns if col not in plot_tab_exclude_cols]
        
        effective_categorical_cols_for_plot_ui = [col for col in categorical_cols if col in effective_cols_for_plot_ui]
        effective_numerical_cols_for_plot_ui = [col for col in numerical_cols if col in effective_cols_for_plot_ui]

        st.markdown("---")
        st.subheader("Configure and Generate Single Plot")
        
        plot_types_available = ["histogram", "kde", "scatter", "bar_chart", "count_plot", "crosstab_heatmap"]
        selected_plot_type = st.selectbox("Select Plot Type:", plot_types_available, key="plot_type_select_main")
        
        plot_params_ui = {}
        
        primary_col_options = effective_cols_for_plot_ui
        if selected_plot_type == "kde":
            primary_col_options = effective_numerical_cols_for_plot_ui
        
        if selected_plot_type != "crosstab_heatmap":
            plot_params_ui['col_name'] = st.selectbox("Primary Column (x-axis):", [None] + primary_col_options, index=0, key="plot_param_col_name_main")
        
        if selected_plot_type in ["kde", "scatter", "bar_chart", "count_plot"]:
            plot_params_ui['hue_col'] = st.selectbox("Hue Column (optional):", [None] + effective_categorical_cols_for_plot_ui, index=0, key="plot_param_hue_col_main")
        
        if selected_plot_type == "histogram":
            primary_col_for_hist = plot_params_ui.get('col_name')
            is_primary_col_numeric = bool(primary_col_for_hist and primary_col_for_hist in effective_numerical_cols_for_plot_ui)
            plot_params_ui['bins'] = st.slider("Bins:", 10, 100, 30, key="hist_bins_main")
            if is_primary_col_numeric:
                plot_params_ui['kde'] = st.checkbox("Overlay KDE?", value=False, key="hist_kde_main")
                if plot_params_ui.get('kde'):
                    plot_params_ui['kde_line_color'] = st.color_picker("KDE Line Color:", "#FF5733", key="hist_kde_line_color_main")
            plot_params_ui['color'] = st.color_picker("Bar Color", "#1f77b4", key="hist_color_main")
            plot_params_ui['stat'] = st.selectbox("Statistic:", ["count", "frequency", "density", "probability"], index=0, key="hist_stat_main")
        
        elif selected_plot_type == "kde":
            plot_params_ui['fill'] = st.checkbox("Fill KDE plot?", value=True, key="kde_fill_main")
            plot_params_ui['alpha'] = st.slider("Alpha:", 0.0, 1.0, 0.7, key="kde_alpha_main")
            plot_params_ui['linewidth'] = st.slider("Line Width:", 0.5, 5.0, 1.5, step=0.5, key="kde_linewidth_main")
        
        elif selected_plot_type == "scatter":
            x_axis_column = plot_params_ui.pop('col_name', None)
            if x_axis_column: plot_params_ui['col_name_x'] = x_axis_column
            
            y_axis_column = st.selectbox("Y-axis Column:", options=[None] + effective_numerical_cols_for_plot_ui, index=0, key="scatter_y_main")
            if y_axis_column: plot_params_ui['col_name_y'] = y_axis_column

            if x_axis_column and x_axis_column in effective_categorical_cols_for_plot_ui:
                st.warning(f"💡 Note: You've selected a categorical column ('{x_axis_column}') for the X-axis. This will generate a strip plot-like visualization.")
            
            plot_params_ui["alpha"] = st.slider("Point Alpha:", 0.0, 1.0, value=0.5, key="scatter_alpha_main")
            plot_params_ui['s'] = st.slider("Point Size (s):", 10, 200, value=50, key="scatter_s_main")
        
        elif selected_plot_type == "bar_chart":
            x_axis_column = plot_params_ui.pop('col_name', None)
            if x_axis_column: plot_params_ui['x_col'] = x_axis_column

            y_axis_column = st.selectbox("Y-axis Column (numerical):", options=[None] + effective_numerical_cols_for_plot_ui, index=0, key="bar_y_main")
            if y_axis_column: plot_params_ui['y_col'] = y_axis_column

            plot_params_ui['estimator'] = st.selectbox("Estimator:", [None, 'mean', 'median', 'sum'], index=0, key="bar_estimator_main")
            plot_params_ui['errorbar'] = st.selectbox("Error Bars:", [None, "sd", "ci", "se", "pi"], index=0, key="bar_errorbar_main")
            user_palette = st.text_input("Color Palette (optional):", "", key="bar_palette_main")
            if user_palette.strip(): plot_params_ui['palette'] = user_palette.strip()
            plot_params_ui['alpha'] = st.slider("Bar Alpha:", 0.1, 1.0, value=1.0, key="bar_alpha_main")

        elif selected_plot_type == "count_plot":
            x_axis_column = plot_params_ui.pop('col_name', None)
            if x_axis_column: plot_params_ui['x_col'] = x_axis_column

            plot_params_ui['dodge'] = st.checkbox("Separate bars by hue", value=True, key="count_dodge_main")
            user_palette = st.text_input("Color Palette (optional):", "", key="count_palette_main")
            if user_palette.strip(): plot_params_ui['palette'] = user_palette.strip()
            plot_params_ui['alpha'] = st.slider("Bar Alpha:", 0.1, 1.0, value=1.0, key="count_alpha_main")

        elif selected_plot_type == "crosstab_heatmap":
            plot_params_ui['index_names_ct'] = st.multiselect("Index (rows):", options=effective_categorical_cols_for_plot_ui, key="heatmap_idx_main")
            plot_params_ui['column_names_ct'] = st.multiselect("Columns:", options=effective_categorical_cols_for_plot_ui, key="heatmap_col_main")
            plot_params_ui['annot'] = st.checkbox("Show values?", value=True, key="heatmap_annot_main")
            if plot_params_ui['annot']:
                plot_params_ui['fmt'] = st.text_input("Value Format:", ".0f", key="heatmap_fmt_main")
            plot_params_ui['cmap'] = st.text_input("Color Map (cmap):", "YlGnBu", key="heatmap_cmap_main")

        if st.button(f"Generate {selected_plot_type}", key="gen_dyn_plot_main"):
            # Validation logic
            ready_to_plot = False
            if selected_plot_type in ["histogram", "kde"] and plot_params_ui.get('col_name'): ready_to_plot = True
            elif selected_plot_type == "scatter" and plot_params_ui.get('col_name_x') and plot_params_ui.get('col_name_y'): ready_to_plot = True
            elif selected_plot_type in ["bar_chart", "count_plot"] and plot_params_ui.get('x_col'): ready_to_plot = True
            elif selected_plot_type == "crosstab_heatmap" and plot_params_ui.get('index_names_ct') and plot_params_ui.get('column_names_ct'): ready_to_plot = True
            
            if ready_to_plot:
                final_plot_params = {k: v for k, v in plot_params_ui.items() if v is not None}
                # Ensure boolean False values from checkboxes are preserved
                for bool_key in ['kde', 'fill', 'annot', 'dodge']:
                    if bool_key in plot_params_ui and plot_params_ui[bool_key] is False:
                        final_plot_params[bool_key] = False

                dynamic_plot_config = [{"type": selected_plot_type, "params": final_plot_params}]
                endpoint_url = f"{FASTAPI_BASE_URL}/plots/dashboard"
                query_params_plots = {}
                if plot_tab_include_cols: query_params_plots["include_columns"] = plot_tab_include_cols
                if plot_tab_exclude_cols: query_params_plots["exclude_columns"] = plot_tab_exclude_cols
                
                try:
                    with st.spinner(f"Generating {selected_plot_type}..."):
                        response = requests.post(endpoint_url, json=dynamic_plot_config, params=query_params_plots) 
                        response.raise_for_status()
                        # MODIFIED FOR OLDER STREAMLIT VERSION
                        st.image(response.content, caption=f"Generated {selected_plot_type}", use_column_width=True)
                except Exception as e:
                    st.error(f"Failed to generate plot. API Error: {e}")
            else: 
                st.warning("Please select all necessary columns/parameters for the chosen plot type.")

# In dashboard.py
# In dashboard.py

with tab_descriptive_stats:
    st.header("Descriptive Statistics")
    
    with st.sidebar.expander("Descriptive Statistics Controls", expanded=True):
        st.subheader("Column Selection for Statistics")
        desc_include_cols = st.multiselect("Include columns:", all_columns, default=None, key="desc_include_main")
        desc_exclude_cols = st.multiselect("Exclude columns for statistics:", all_columns, default=None, key="desc_exclude_main")

    query_params_for_desc_tab = {}
    if desc_include_cols: query_params_for_desc_tab["include_columns"] = desc_include_cols
    if desc_exclude_cols: query_params_for_desc_tab["exclude_columns"] = desc_exclude_cols

    # --- Define All Sections for this Tab ---
    sections = {
        "Numerical Summary": {"endpoint": "numerical-summary", "state_var": "show_numerical_summary"},
        "Categorical Summary": {"endpoint": "categorical-summary", "state_var": "show_categorical_summary"},
        "Unique Value Counts": {"endpoint": "unique-counts", "state_var": "show_unique_counts"},
        "Dataset Shape": {"endpoint": "shape", "state_var": "show_dataset_shape"},
        "Dataset Info": {"endpoint": "info", "state_var": "show_dataset_info"},
        "Frequency Table": {"endpoint": "frequency-table", "state_var": "show_frequency_table_section"},
        "Cross-Tabulations": {"endpoint": "cross-tabs", "state_var": "show_crosstab_section"}
    }

    ### START: NEW CALLBACK FUNCTION AND MODIFIED BUTTON LOGIC ###

    # Define a callback function to handle the button click logic
    def handle_accordion_button_click(clicked_state_var):
        # Determine the intended new state for the section that was clicked
        # (i.e., if it was 'False', the new state is 'True')
        new_state = not st.session_state.get(clicked_state_var, False)
        
        # First, reset all section visibility states to False
        for config in sections.values():
            st.session_state[config["state_var"]] = False
        
        # Now, apply the intended new state to the section that was clicked
        st.session_state[clicked_state_var] = new_state

    # Loop to create and handle all sections
    for title, config in sections.items():
        st.subheader(title)
        state_var = config["state_var"]
        
        button_label = f"Hide {title}" if st.session_state.get(state_var, False) else f"Show {title}"
        
        # Use the on_click parameter to call our function. This is the correct pattern.
        st.button(
            button_label, 
            key=f"btn_toggle_{state_var}",
            on_click=handle_accordion_button_click,
            args=(state_var,) # Pass the specific state variable key to the callback
        )
            
        # Display content if this section is toggled open
        if st.session_state.get(state_var, False):
            # This block is now only for displaying content, not for changing state.
            try:
                # Specific UI and API call logic for each section type
                if title == "Frequency Table":
                    if not categorical_cols:
                        st.info("No categorical columns available for this operation.")
                    else:
                        selected_col_freq = st.selectbox("Select column:", categorical_cols, key="freq_table_col_select")
                        if st.button("Generate Frequency Table", key="btn_gen_freq_table"):
                            endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/{config['endpoint']}"
                            api_params = query_params_for_desc_tab.copy()
                            api_params["column_name"] = selected_col_freq
                            with st.spinner(f"Fetching {title}..."):
                                response = requests.get(endpoint_url, params=api_params)
                                response.raise_for_status()
                                display_df_from_api_split_response(response.json(), f"{title} for '{selected_col_freq}'.", index_level_names=[selected_col_freq])
                
                elif title == "Cross-Tabulations":
                    if not categorical_cols:
                        st.info("No categorical columns available for this operation.")
                    else:
                        index_cols = st.multiselect("Index Column(s):", categorical_cols, key="crosstab_index")
                        column_cols = st.multiselect("Column(s):", categorical_cols, key="crosstab_columns")
                        normalize = st.checkbox("Normalize Crosstab?", value=False, key="crosstab_normalize")
                        margins = st.checkbox("Show Margins?", value=False, key="crosstab_margins")

                        if st.button("Generate Cross-Tabulation", key="btn_gen_crosstab_table"):
                            if not index_cols or not column_cols:
                                st.warning("Please select at least one index AND one column.")
                            else:
                                endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/{config['endpoint']}" 
                                payload = {"index_names": index_cols, "column_names": column_cols, "normalize": normalize, "margins": margins}
                                with st.spinner(f"Generating {title}..."):
                                    response = requests.post(endpoint_url, json=payload, params=query_params_for_desc_tab)
                                    response.raise_for_status() 
                                    display_df_from_api_split_response(response.json(), "Crosstab loaded.", index_level_names=index_cols)
                
                else: # Logic for the other summary sections
                    endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/{config['endpoint']}"
                    with st.spinner(f"Fetching {title}..."):
                        response = requests.get(endpoint_url, params=query_params_for_desc_tab)
                    response.raise_for_status()
                    response_data = response.json()

                    # Simplified display logic, assuming 'split_df' for the first two
                    if title in ["Numerical Summary", "Categorical Summary", "Dataset Shape"]:
                        display_df_from_api_split_response(response_data, f"{title}.")
                    elif title == "Unique Value Counts":
                        st.json(response_data.get("counts", {}))
                        st.success(f"{title} loaded.")
                    elif title == "Dataset Info":
                        st.text_area(f"{title}", response_data.get("info_string", "No info available."), height=300)
                        st.success(f"{title} loaded.")

            except Exception as e:
                st.error(f"API Error ({title}): {e}")
                st.session_state[state_var] = False
        
        st.markdown("---")
    ### END: REVISED BUTTON LOGIC ###


with tab_data_view:
    st.header("View and Filter Data Subset")
    with st.sidebar.expander("Data View & Filter Controls", expanded=True):
        st.subheader("Row Filters")
        filter_col = st.selectbox("Filter by column:", [None] + all_columns, index=0, key="filter_col_select_view")
        filter_val = "" 
        if filter_col:
            filter_val = st.text_input(f"Enter value to filter for in '{filter_col}':", key="filter_value_input_view")
        st.subheader("Column Selection")
        view_include_cols = st.multiselect("Include columns:", all_columns, default=all_columns, key="view_tab_include")
        view_exclude_cols = st.multiselect("Exclude columns:", all_columns, default=None, key="view_tab_exclude")

    if st.checkbox("Show Filtered/Shaped Data", key="toggle_filtered_data"):
        endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/filter" 
        payload = {"cols": [], "values": []}
        if filter_col and filter_val.strip(): 
            payload["cols"] = [filter_col]
            payload["values"] = [filter_val] 
        query_params = {}
        if view_include_cols: query_params["include_columns"] = view_include_cols
        if view_exclude_cols: query_params["exclude_columns"] = view_exclude_cols
        
        with st.spinner("Fetching filtered data..."):
            try:
                response = requests.post(endpoint_url, json=payload, params=query_params)
                response.raise_for_status()
                response_data = response.json() 
                if "records" in response_data:
                    df_filtered = pd.DataFrame.from_records(response_data["records"])
                    st.dataframe(df_filtered)
                    st.success(f"Filtered data loaded. Displaying {len(df_filtered)} rows.")
                    if df_filtered.empty:
                        st.info("The current filter and/or column selection resulted in no data.")
                else:
                    st.warning("Filtered data is empty or not in expected 'records' format.")
                    st.json(response_data)
            except Exception as e:
                st.error(f"API Error (Filtered Data): {e}")