# dashboard.py - Final Corrected Version
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
    # --- Validation ---
    if not isinstance(response_data_split, dict) or any(k not in response_data_split for k in ['index', 'columns', 'data']):
        st.error(f"API Error for '{success_message}': Invalid data format received from API.")
        st.json({"unexpected_response": response_data_split})
        return
    
    # --- DataFrame Reconstruction and Display ---
    try:
        index_from_json = response_data_split['index']
        columns_from_json = response_data_split['columns']
        data_from_json = response_data_split['data']
        
        # This correctly reconstructs the DataFrame from the API response
        df_display = pd.DataFrame(data=data_from_json, index=index_from_json, columns=columns_from_json)
        
        # This check prevents the error by only setting index names if they are provided
        if index_level_names is not None:
            df_display.index.names = index_level_names

        # This part fixes the Arrow serialization warning from your terminal
        for col in df_display.columns:
            if df_display[col].dtype == 'object':
                df_display[col] = df_display[col].astype(str)

        # Display the final, corrected DataFrame
        st.dataframe(df_display)
        st.success(success_message)

    except Exception as e: 
        st.error(f"Error displaying DataFrame for '{success_message}': {e}")
        traceback.print_exc()

# --- Session State Initialization ---
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.active_dataset = "diamonds"
    
    # Initialize all UI visibility toggles to False
    st.session_state.show_numerical_summary = False
    st.session_state.show_categorical_summary = False
    st.session_state.show_unique_counts = False
    st.session_state.show_dataset_info = False
    st.session_state.show_frequency_table_section = False
    st.session_state.show_crosstab_section = False
    
    # Initialize the states for the filter widgets as empty lists
    st.session_state.dashboard_include_cols = []
    st.session_state.dashboard_exclude_cols = []

    st.session_state.saved_plot_configs = []
    
    st.rerun()
# --- Data-Dependent State ---
column_data = get_column_data_from_api() 
if column_data:
    st.session_state.all_columns = column_data.get("all_columns", [])
    st.session_state.numerical_cols = column_data.get("numerical_columns", [])
    st.session_state.categorical_cols = column_data.get("categorical_columns", [])
else: 
    st.session_state.all_columns, st.session_state.numerical_cols, st.session_state.categorical_cols = [], [], []

all_columns: List[str] = st.session_state.get('all_columns', [])
numerical_cols: List[str] = st.session_state.get('numerical_cols', [])
categorical_cols: List[str] = st.session_state.get('categorical_cols', [])

# --- Sidebar UI ---
st.sidebar.title("Controls & Options")

# In dashboard.py, inside the sidebar
# In dashboard.py

# In your dashboard.py file

with st.sidebar.expander("Column Filters (for Plots & Statistics)", expanded=True):
    selection_mode = st.radio(
        "Filter columns by:",
        ["Excluding selected columns", "Including selected columns"],
        key="column_selection_mode",
        index=0 
    )

    if selection_mode == "Including selected columns":
        st.caption("Choose the specific columns to use for all plots and statistics.")
        include_cols = st.multiselect(
            "Columns to Include:", 
            options=all_columns, 
            key="dashboard_include_cols",
            default= [],
        )
        exclude_cols = []
    
    else: # Excluding selected columns
        st.caption("All columns are included by default. Choose any to remove from the list.")
        # This multiselect's state is controlled by the key "dashboard_exclude_mode_selector"
        # and its output is the list of columns the user wants to KEEP.
        kept_cols = st.multiselect(
            "Visible Columns:", 
            options=all_columns, 
            default=all_columns,
            key="dashboard_exclude_mode_selector" 
        )
        include_cols = kept_cols
        exclude_cols = [col for col in all_columns if col not in kept_cols]
        

    # --- This callback function is now corrected ---
    def reset_column_filters():
        # It now clears the state for the correct widget keys
        st.session_state.dashboard_include_cols = []
        st.session_state.dashboard_exclude_mode_selector = all_columns # <<< This was the line with the typo
    
    st.button("Reset Column Filters", on_click=reset_column_filters)
# --- Main Page Content ---
st.markdown("### Select a Dataset")
available_datasets = get_available_datasets()
if available_datasets:
    try:
        default_index = available_datasets.index(st.session_state.active_dataset)
    except (ValueError, TypeError):
        default_index = 0
    selected_dataset = st.selectbox("Choose a dataset to analyze:", available_datasets, index=default_index, key="dataset_selector")

    if selected_dataset and (selected_dataset != st.session_state.active_dataset):
        with st.spinner(f"Loading '{selected_dataset}'..."):
            try:
                response = requests.post(f"{FASTAPI_BASE_URL}/datasets/select/{selected_dataset}")
                response.raise_for_status()
                new_active_dataset = selected_dataset
                protected_keys = ['app_initialized', 'column_selection_mode'] 
                for key in list(st.session_state.keys()):
                    if key not in protected_keys:
                        del st.session_state[key]
                st.session_state.active_dataset = new_active_dataset
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to switch dataset: {e}")
else:
    st.warning("No datasets discovered.")

st.markdown("---")

tab_plots, tab_descriptive_stats = st.tabs(["📊 Plot Dashboard", "🔢 Descriptive Statistics"])

# Determine effective columns once, based on the single global sidebar filter
effective_cols = list(all_columns)
if include_cols:
    effective_cols = [col for col in all_columns if col in include_cols]
elif exclude_cols:
    effective_cols = [col for col in all_columns if col not in exclude_cols]
effective_categorical_cols = [col for col in categorical_cols if col in effective_cols]
effective_numerical_cols = [col for col in numerical_cols if col in effective_cols]

with tab_plots:
    st.header("Plot Generation")
    with st.expander("Configure Plot", expanded=True):
        st.subheader("1. Select Plot Type and Axes")
        plot_types_available = ["histogram", "kde", "scatter", "bar_chart", "count_plot", "crosstab_heatmap"]
        selected_plot_type = st.selectbox("Plot Type:", plot_types_available, key="plot_type_select")
        
        plot_params = {}
        primary_col_options = {
            "kde": effective_numerical_cols,
            "count_plot": effective_categorical_cols,
            "bar_chart": effective_categorical_cols
        }.get(selected_plot_type, effective_cols)

        if selected_plot_type != "crosstab_heatmap":
            x_selection = st.selectbox("Primary Column (x-axis):", [None] + primary_col_options, key="plot_param_x_axis")
            if selected_plot_type in ["bar_chart", "count_plot"]: plot_params['x_col'] = x_selection
            elif selected_plot_type == "scatter": plot_params['col_name_x'] = x_selection
            else: plot_params['col_name'] = x_selection

        if selected_plot_type in ["scatter", "bar_chart"]:
            y_selection = st.selectbox("Y-axis Column (numerical):", [None] + effective_numerical_cols, key="plot_param_y_axis")
            if selected_plot_type == "scatter": plot_params['col_name_y'] = y_selection
            elif selected_plot_type == "bar_chart": plot_params['y_col'] = y_selection
        
        if selected_plot_type in ["kde", "scatter", "bar_chart", "count_plot"]:
            plot_params['hue_col'] = st.selectbox("Hue (optional):", [None] + effective_categorical_cols, key="plot_param_hue_col")
        
        st.markdown("---")
        st.subheader("2. Adjust Plot-Specific Options")
        
        palette_options = [None, 'pastel', 'husl', 'Set2', 'flare', 'viridis', 'mako']

        if selected_plot_type == "histogram":
            is_numeric = bool(plot_params.get('col_name') and plot_params.get('col_name') in effective_numerical_cols)
            plot_params['bins'] = st.slider("Bins:", 10, 100, 30, key="hist_bins")
            if is_numeric:
                plot_params['kde'] = st.checkbox("Overlay KDE?", key="hist_kde")
                if plot_params.get('kde'):
                    plot_params['kde_line_color'] = st.color_picker("KDE Line Color:", "#FF5733", key="hist_kde_color")
            plot_params['color'] = st.color_picker("Bar Color", "#1f77b4", key="hist_color")
            plot_params['stat'] = st.selectbox("Statistic:", ["count", "frequency", "density", "probability"], key="hist_stat", help="The aggregate statistic for each bar.")
        
        elif selected_plot_type == "kde":
            plot_params['fill'] = st.checkbox("Fill KDE plot?", value=True, key="kde_fill")
            plot_params['alpha'] = st.slider("Alpha:", 0.0, 1.0, 0.7, key="kde_alpha")
            plot_params['linewidth'] = st.slider("Line Width:", 0.5, 5.0, 1.5, key="kde_linewidth")
        
        elif selected_plot_type == "scatter":
            if plot_params.get('col_name_x') and plot_params.get('col_name_x') in effective_categorical_cols:
                st.warning(f"💡 Note: X-axis is categorical. This will produce a strip plot-like visualization.")
            plot_params["alpha"] = st.slider("Point Alpha:", 0.0, 1.0, value=0.5, key="scatter_alpha")
            plot_params['s'] = st.slider("Point Size:", 10, 200, value=50, key="scatter_s")
        
        elif selected_plot_type == "bar_chart":
            plot_params['estimator'] = st.selectbox("Estimator:", ['mean', 'median', 'sum'], key="bar_estimator", help="Method for aggregating the Y-axis value.")
            plot_params['errorbar'] = st.selectbox("Error Bars:", [None, "sd", "ci", "se", "pi"], key="bar_errorbar", help="Show uncertainty around the bar's height.")
            plot_params['palette'] = st.selectbox("Color Palette:", options=palette_options, key="bar_palette")
            plot_params['alpha'] = st.slider("Bar Alpha:", 0.1, 1.0, value=1.0, key="bar_alpha")

        elif selected_plot_type == "count_plot":
            plot_params['dodge'] = st.checkbox("Separate bars by hue", value=True, key="count_dodge")
            plot_params['palette'] = st.selectbox("Color Palette:", options=palette_options, key="count_palette")
            plot_params['alpha'] = st.slider("Bar Alpha:", 0.1, 1.0, value=1.0, key="count_alpha")

        elif selected_plot_type == "crosstab_heatmap":
            plot_params['index_names_ct'] = st.multiselect("Index (rows):", options=effective_categorical_cols, key="heatmap_idx")
            plot_params['column_names_ct'] = st.multiselect("Columns:", options=effective_categorical_cols, key="heatmap_col")
            plot_params['annot'] = st.checkbox("Show values?", value=True, key="heatmap_annot")
            if plot_params.get('annot'):
                plot_params['fmt'] = st.text_input("Value Format:", ".0f", key="heatmap_fmt")
            plot_params['cmap'] = st.text_input("Color Map:", "YlGnBu", key="heatmap_cmap")

    st.markdown("---")
    if st.button(f"Generate {selected_plot_type}", key="gen_dyn_plot"):
        ready_to_plot = False
        if selected_plot_type in ["histogram", "kde"] and plot_params.get('col_name'): ready_to_plot = True
        elif selected_plot_type == "scatter" and plot_params.get('col_name_x') and plot_params.get('col_name_y'): ready_to_plot = True
        elif selected_plot_type in ["bar_chart", "count_plot"] and plot_params.get('x_col'): ready_to_plot = True
        elif selected_plot_type == "crosstab_heatmap" and plot_params.get('index_names_ct') and plot_params.get('column_names_ct'): ready_to_plot = True
        
        if ready_to_plot:
            final_plot_params = {k: v for k, v in plot_params.items() if v is not None}
            for bool_key in ['kde', 'fill', 'annot', 'dodge']:
                if bool_key in plot_params and plot_params[bool_key] is False:
                    final_plot_params[bool_key] = False
            
            dynamic_plot_config = [{"type": selected_plot_type, "params": final_plot_params}]
            query_params_plots = {"include_columns": include_cols, "exclude_columns": exclude_cols}
            try:
                with st.spinner(f"Generating {selected_plot_type}..."):
                    response = requests.post(f"{FASTAPI_BASE_URL}/plots/dashboard", json=dynamic_plot_config, params=query_params_plots) 
                    response.raise_for_status()
                    st.image(response.content, caption=f"Generated {selected_plot_type}", use_column_width=True)
            except Exception as e:
                st.error(f"Failed to generate plot. API Error: {e}")
        else: 
            st.warning("Please select all necessary columns/parameters for the chosen plot type.")

with tab_descriptive_stats:
    st.header("Descriptive Statistics")
    
    query_params_for_desc_tab = {"include_columns": include_cols, "exclude_columns": exclude_cols}
    
    sections = {
        "Numerical Summary": {"endpoint": "numerical-summary", "state_var": "show_numerical_summary", "response_type": "split_df"},
        "Categorical Summary": {"endpoint": "categorical-summary", "state_var": "show_categorical_summary", "response_type": "split_df"},
        "Unique Value Counts": {"endpoint": "unique-counts", "state_var": "show_unique_counts", "response_type": "json_counts"},
        "Dataset Info": {"endpoint": "info", "state_var": "show_dataset_info", "response_type": "text_area_info"},
        "Frequency Table": {"endpoint": "frequency-table", "state_var": "show_frequency_table_section"},
        "Cross-Tabulations": {"endpoint": "cross-tabs", "state_var": "show_crosstab_section"}
    }
    
    def handle_independent_toggle(state_key):
        st.session_state[state_key] = not st.session_state.get(state_key, False)

    for title, config in sections.items():
        st.subheader(title)
        state_var = config["state_var"]
        button_label = f"Hide {title}" if st.session_state.get(state_var, False) else f"Show {title}"
        st.button(button_label, key=f"btn_toggle_{state_var}", on_click=handle_independent_toggle, args=(state_var,))
            
        if st.session_state.get(state_var, False):
            endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/{config['endpoint']}"
            try:
                # Sections with their own UI and "Generate" button
                if title == "Frequency Table":
                    if not categorical_cols: st.info("No categorical columns available.")
                    else:
                        selected_col_freq = st.selectbox("Select column:", effective_categorical_cols, key="freq_table_col_select")
                        if st.button("Generate Frequency Table", key="btn_gen_freq_table"):
                            api_params = query_params_for_desc_tab.copy()
                            api_params["column_name"] = selected_col_freq
                            with st.spinner("Fetching..."):
                                response = requests.get(endpoint_url, params=api_params)
                                response.raise_for_status()
                                display_df_from_api_split_response(response.json(), f"Table for '{selected_col_freq}'.")
                
                elif title == "Cross-Tabulations":
                    if not categorical_cols: st.info("No categorical columns available.")
                    else:
                        index_cols = st.multiselect("Index Column(s):", effective_categorical_cols, key="crosstab_index")
                        column_cols = st.multiselect("Column(s):", effective_categorical_cols, key="crosstab_columns")
                        normalize = st.checkbox("Normalize?", key="crosstab_normalize")
                        margins = st.checkbox("Show Margins?", key="crosstab_margins")
                        if st.button("Generate Cross-Tabulation", key="btn_gen_crosstab_table"):
                            if not index_cols or not column_cols: st.warning("Please select at least one index AND one column.")
                            else:
                                payload = {"index_names": index_cols, "column_names": column_cols, "normalize": normalize, "margins": margins}
                                with st.spinner("Generating..."):
                                    response = requests.post(endpoint_url, json=payload, params=query_params_for_desc_tab)
                                    response.raise_for_status() 
                                    display_df_from_api_split_response(response.json(), "Crosstab loaded.", index_level_names=index_cols)
                
                # Sections that load automatically when shown
                else: 
                    with st.spinner(f"Fetching {title}..."):
                        response = requests.get(endpoint_url, params=query_params_for_desc_tab)
                    response.raise_for_status()
                    response_data = response.json()
                    
                    response_type = config.get("response_type")
                    if response_type == "split_df": display_df_from_api_split_response(response_data, f"{title}.")
                    elif response_type == "json_counts": st.json(response_data.get("counts", {}))
                    elif response_type == "json_direct": st.json(response_data)
                    elif response_type == "text_area_info": st.text_area(f"{title}", response_data.get("info_string", ""), height=300)
                    st.success(f"{title} loaded.")
            except Exception as e:
                st.error(f"API Error ({title}): {e}")
                st.session_state[state_var] = False
        st.markdown("---")