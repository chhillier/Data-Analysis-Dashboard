# dashboard.py - FINAL VERSION
import streamlit as st
import requests
import pandas as pd
from typing import List, Dict, Any, Optional

# --- Configuration ---
FASTAPI_BASE_URL = "http://localhost:8000/api"

st.set_page_config(layout="wide", page_title="Data Analysis Dashboard")

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
@st.cache_data(ttl=30)
def get_saved_dashboards() -> List[str]:
    """Fetches the list of saved dashboard files from the API."""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/dashboards")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Could not fetch saved dashboards: {e}")
        return []
def display_df_from_api_split_response(response_data_split: Dict[str, Any], success_message: str = "Data loaded.", index_level_names: Optional[List[str]] = None):
    """Reconstructs and displays a DataFrame from a 'split' format JSON response."""
    if not isinstance(response_data_split, dict) or any(k not in response_data_split for k in ['index', 'columns', 'data']):
        st.error(f"API Error for '{success_message}': Invalid data format received.")
        st.json({"unexpected_response": response_data_split})
        return
    try:
        df_display = pd.DataFrame(data=response_data_split['data'], index=response_data_split['index'], columns=response_data_split['columns'])
        if index_level_names:
            df_display.index.names = index_level_names
        for col in df_display.columns:
            if df_display[col].dtype == 'object':
                df_display[col] = df_display[col].astype(str)
        st.dataframe(df_display)
        st.success(success_message)
    except Exception as e:
        st.error(f"Error displaying DataFrame for '{success_message}': {e}")

# --- Session State Initialization ---
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.active_dataset = "diamonds"
    st.session_state.show_numerical_summary = False
    st.session_state.show_categorical_summary = False
    st.session_state.show_unique_counts = False
    st.session_state.show_dataset_info = False
    st.session_state.show_frequency_table_section = False
    st.session_state.show_crosstab_section = False
    st.session_state.saved_plot_configs = []
    st.session_state.last_generated_plot_config = None
    st.session_state.last_generated_plot_image = None
    st.session_state.display_mode_active = False
    st.session_state.custom_dashboard_image = None
    st.session_state.include_cols = []
    st.rerun()

# --- Data-Dependent State ---
column_data = get_column_data_from_api()
if column_data:
    all_columns = column_data.get("all_columns", [])
    numerical_cols = column_data.get("numerical_columns", [])
    categorical_cols = column_data.get("categorical_columns", [])
else:
    all_columns, numerical_cols, categorical_cols = [], [], []

if 'visible_cols' not in st.session_state or st.session_state.get('active_dataset_changed', False):
    st.session_state.visible_cols = all_columns
    st.session_state.active_dataset_changed = False


# --- Main App Logic ---
def exit_display_mode():
    st.session_state.display_mode_active = False
    st.session_state.custom_dashboard_image = None
    st.session_state.include_cols = []
    st.session_state.visible_cols = all_columns

include_cols = st.session_state.get('include_cols', [])
visible_cols = st.session_state.get('visible_cols', all_columns)

if include_cols:
    effective_cols = include_cols
else:
    effective_cols = visible_cols

effective_categorical_cols = [col for col in categorical_cols if col in effective_cols]
effective_numerical_cols = [col for col in numerical_cols if col in effective_cols]


if st.session_state.get('display_mode_active', False):
    # --- DISPLAY MODE UI ---
    st.title("🖼️ Custom Dashboard View")
    st.button("⬅️ Return to Configuration", on_click=exit_display_mode)
    st.markdown("---")
    if st.session_state.get('custom_dashboard_image'):
        st.image(st.session_state.custom_dashboard_image, caption="Your Custom Generated Dashboard", use_column_width=True)
    else:
        st.warning("No dashboard image found. Returning to configuration.")
        exit_display_mode()
        st.rerun()
else:
    # --- CONFIGURATION MODE UI ---
    st.title("📊 Data Analysis Dashboard")

    # --- Sidebar UI ---
    st.sidebar.title("Controls & Options")
    
    with st.sidebar.expander("💾 Save & Load Dashboard", expanded=True):
    
        # --- LOAD ---
        st.subheader("Load Configuration")
        saved_dashboards_list = get_saved_dashboards()
        selected_dashboard_to_load = st.selectbox(
            "Select a saved dashboard:",
            options=[""] + saved_dashboards_list,
            key="dashboard_loader_select"
        )

        def handle_dashboard_load():
            """Callback to load a selected dashboard state."""
            filename = st.session_state.dashboard_loader_select
            if not filename:
                return
            
            try:
                response = requests.get(f"{FASTAPI_BASE_URL}/dashboards/{filename}")
                response.raise_for_status()
                loaded_state = response.json()
                
                new_dataset = loaded_state['dataset_name']
                requests.post(f"{FASTAPI_BASE_URL}/datasets/select/{new_dataset}").raise_for_status()

                st.session_state.active_dataset = new_dataset
                st.session_state.saved_plot_configs = loaded_state['plot_configs']
                st.session_state.include_cols = loaded_state['filter_state']['include_cols']
                st.session_state.visible_cols = loaded_state['filter_state']['visible_cols']
                st.session_state.active_dataset_changed = True
                
                st.cache_data.clear()
                st.session_state.dashboard_loader_select = ""
                st.success(f"Dashboard '{filename}' loaded!")
                
            except Exception as e:
                st.error(f"Failed to load dashboard: {e}")

        st.button("Load Selected", on_click=handle_dashboard_load, disabled=(not selected_dashboard_to_load))

        st.markdown("---")

        # --- SAVE ---
        st.subheader("Save Current Configuration")
        save_filename = st.text_input("Save as (e.g., my-analysis):", key="dashboard_saver_input")
        
        def handle_dashboard_save():
            """Callback to save the current dashboard state."""
            filename = st.session_state.dashboard_saver_input
            if not filename:
                st.warning("Please enter a filename.")
                return

            current_state = {
                "dataset_name": st.session_state.active_dataset,
                "plot_configs": st.session_state.saved_plot_configs,
                "filter_state": {
                    "include_cols": st.session_state.include_cols,
                    "visible_cols": st.session_state.visible_cols
                }
            }

            try:
                response = requests.post(f"{FASTAPI_BASE_URL}/dashboards/save/{filename}", json=current_state)
                response.raise_for_status()
                st.success(f"Dashboard saved as '{filename}.json'")
                get_saved_dashboards.clear()
                st.session_state.dashboard_saver_input = ""
            except Exception as e:
                st.error(f"Failed to save dashboard: {e}")

        st.button("Save", on_click=handle_dashboard_save, disabled=(not save_filename))

        st.markdown("---")
        st.subheader("Delete Configuration")
        dashboard_to_delete = st.selectbox(
            "Select a dashboard to delete:",
            options=[""] + saved_dashboards_list,
            key="dashboard_deleter_select"
        )
        def handle_dashboard_delete():
            """Callback to delete a saved dashboard file."""
            filename = st.session_state.dashboard_deleter_select
            if not filename:
                return
            try:
                response = requests.delete(f"{FASTAPI_BASE_URL}/dashboards/delete/{filename}")
                response.raise_for_status()
                st.success(f"Dashboard '{filename}' deleted.")
                get_saved_dashboards.clear()
                st.session_state.dashboard_deleter_select = ""
            except Exception as e:
                st.error(f"Failed to delete dashboard: {e}")
        st.button(
            "Delete Selected",
            on_click=handle_dashboard_delete,
            disabled= (not dashboard_to_delete),
            type="primary"
        )

    
    with st.sidebar.expander("Column Filters", expanded=True):
        st.info("💡 'Include' filter takes priority over the 'Visible' filter.")

        st.subheader("Include Specific Columns")
        # new_dashboard.py (in the sidebar)

        # Define the callback for this button
        def clear_include_selections():
            st.session_state.include_cols = []

        st.multiselect(
            "Only show these columns:",
            options=all_columns,
            key="include_cols",
            help="If you select any columns here, only these will be used."
        )

        # Attach the callback to the button using on_click
        if st.button("Clear Include Selections", on_click=clear_include_selections, key="reset_include"):
            pass
        
        st.subheader("Filter Visible Columns")

        def reset_visible_columns():
            st.session_state.visible_cols = all_columns

        st.multiselect(
            "Select columns to display:",
            options=all_columns,
            key="visible_cols",
            help="De-select columns here to hide them. Ignored if 'Include' is used."
        )
        if st.button("Reset Visible Columns", on_click=reset_visible_columns, key="reset_visible"):
            pass

    st.sidebar.markdown("---")
    st.sidebar.subheader("My Custom Dashboard")
    num_saved_plots = len(st.session_state.get('saved_plot_configs', []))
    st.sidebar.metric("Saved Plots", num_saved_plots)
    
    if st.sidebar.button("Generate My Custom Dashboard", disabled=(num_saved_plots == 0)):
        if num_saved_plots > 0:
            with st.spinner("Generating..."):
                try:
                    query_params_plots = { "include_columns": effective_cols, "exclude_columns": [] }
                    response = requests.post(f"{FASTAPI_BASE_URL}/plots/dashboard", json=st.session_state.saved_plot_configs, params=query_params_plots)
                    response.raise_for_status()
                    st.session_state.custom_dashboard_image = response.content
                    st.session_state.display_mode_active = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate custom dashboard: {e}")

    if num_saved_plots > 0:
        if st.sidebar.button("Clear Saved Plots"):
            st.session_state.saved_plot_configs = []
            st.rerun()

    # <<< KEY CHANGE: The entire dataset switching logic is now here. >>>
    
    # 1. Define the callback function. Note its indentation is at the top level of the script logic.
    def handle_dataset_change():
        new_dataset = st.session_state.dataset_selector
        with st.spinner(f"Loading '{new_dataset}'..."):
            try:
                response = requests.post(f"{FASTAPI_BASE_URL}/datasets/select/{new_dataset}")
                response.raise_for_status()
                st.session_state.active_dataset = new_dataset
                st.session_state.active_dataset_changed = True
                st.session_state.include_cols = []
                st.session_state.saved_plot_configs = []
                st.session_state.last_generated_plot_config = None
                st.session_state.last_generated_plot_image = None
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Failed to switch dataset: {e}")

    # 2. Define the UI elements.
    st.markdown("### Select a Dataset")
    available_datasets = get_available_datasets()
    if available_datasets:
        try:
            default_index = available_datasets.index(st.session_state.active_dataset)
        except (ValueError, TypeError):
            default_index = 0

        st.selectbox(
            "Choose a dataset:",
            available_datasets,
            index=default_index,
            key="dataset_selector",
            on_change=handle_dataset_change # The callback is attached here
        )
    # The old 'if selected_dataset...' block is now gone.

    st.markdown("---")
    tab_plots, tab_descriptive_stats = st.tabs(["📊 Plot Dashboard", "🔢 Descriptive Statistics"])

    with tab_plots:
        # (The rest of your code for this tab...)
        with st.expander("Configure and Generate a Single Plot", expanded=True):
            st.subheader("1. Select Plot Type and Axes")
            plot_types_available = ["histogram", "kde", "scatter", "bar_chart", "count_plot", "crosstab_heatmap"]
            selected_plot_type = st.selectbox("Plot Type:", plot_types_available, key="plot_type_select")
            plot_params = {}
            primary_col_options = {"kde": effective_numerical_cols, "count_plot": effective_categorical_cols, "bar_chart": effective_categorical_cols}.get(selected_plot_type, effective_cols)
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
                    if plot_params.get('kde'): plot_params['kde_line_color'] = st.color_picker("KDE Line Color:", "#FF5733", key="hist_kde_color")
                plot_params['color'] = st.color_picker("Bar Color", "#1f77b4", key="hist_color")
                plot_params['stat'] = st.selectbox("Statistic:", ["count", "frequency", "density", "probability"], key="hist_stat")
            elif selected_plot_type == "kde":
                plot_params['fill'] = st.checkbox("Fill KDE plot?", value=True, key="kde_fill")
                plot_params['alpha'] = st.slider("Alpha:", 0.0, 1.0, 0.7, key="kde_alpha")
                plot_params['linewidth'] = st.slider("Line Width:", 0.5, 5.0, 1.5, key="kde_linewidth")
            elif selected_plot_type == "scatter":
                if plot_params.get('col_name_x') and plot_params.get('col_name_x') in effective_categorical_cols: st.warning("💡 Note: X-axis is categorical.")
                plot_params["alpha"] = st.slider("Point Alpha:", 0.0, 1.0, value=0.5, key="scatter_alpha")
                plot_params['s'] = st.slider("Point Size:", 10, 200, value=50, key="scatter_s")
            elif selected_plot_type == "bar_chart":
                plot_params['estimator'] = st.selectbox("Estimator:", ['mean', 'median', 'sum'], key="bar_estimator")
                plot_params['errorbar'] = st.selectbox("Error Bars:", [None, "sd", "ci", "se", "pi"], key="bar_errorbar")
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
                if plot_params.get('annot'): plot_params['fmt'] = st.text_input("Value Format:", ".0f", key="heatmap_fmt")
                plot_params['cmap'] = st.text_input("Color Map:", "YlGnBu", key="heatmap_cmap")

            st.markdown("---")
            if st.button("Generate Single Plot", key="gen_dyn_plot"):
                ready_to_plot = False
                if selected_plot_type in ["histogram", "kde"] and plot_params.get('col_name'): ready_to_plot = True
                elif selected_plot_type == "scatter" and plot_params.get('col_name_x') and plot_params.get('col_name_y'): ready_to_plot = True
                elif selected_plot_type in ["bar_chart", "count_plot"] and plot_params.get('x_col'): ready_to_plot = True
                elif selected_plot_type == "crosstab_heatmap" and plot_params.get('index_names_ct') and plot_params.get('column_names_ct'): ready_to_plot = True
                
                if ready_to_plot:
                    final_plot_params = {k: v for k, v in plot_params.items() if v is not None}
                    for bool_key in ['kde', 'fill', 'annot', 'dodge']:
                        if bool_key in plot_params and not plot_params[bool_key]: final_plot_params[bool_key] = False
                    
                    dynamic_plot_config = [{"type": selected_plot_type, "params": final_plot_params}]
                    try:
                        with st.spinner(f"Generating {selected_plot_type}..."):
                            api_params = {"include_columns": effective_cols, "exclude_columns": []}
                            response = requests.post(f"{FASTAPI_BASE_URL}/plots/dashboard", json=dynamic_plot_config, params=api_params)
                            response.raise_for_status()
                            st.session_state.last_generated_plot_config = dynamic_plot_config[0]
                            st.session_state.last_generated_plot_image = response.content
                    except Exception as e:
                        st.error(f"Failed to generate plot: {e}")
                        st.session_state.last_generated_plot_config = None
                        st.session_state.last_generated_plot_image = None
                else:
                    st.warning("Please select all necessary columns/parameters.")

        st.markdown("---")
        st.subheader("Last Generated Plot")
        if st.session_state.get('last_generated_plot_image'):
            st.image(st.session_state.last_generated_plot_image, caption="Last Generated Plot", use_column_width=True)
            config_str = str(st.session_state.get('last_generated_plot_config', ''))
            add_button_key = f"add_plot_{hash(config_str)}"
            if st.button("Add Plot to My Dashboard", key=add_button_key):
                plot_config = st.session_state.last_generated_plot_config
                if plot_config and plot_config not in st.session_state.saved_plot_configs:
                    st.session_state.saved_plot_configs.append(plot_config)
                    st.success(f"Plot configuration saved!")
                    st.session_state.last_generated_plot_config = None
                    st.session_state.last_generated_plot_image = None
                    st.rerun()
                elif not plot_config:
                    st.warning("Could not save plot.")
                else:
                    st.warning("This plot is already saved.")
        else:
            st.info("Your most recently generated plot will appear here.")
            
    with tab_descriptive_stats:
        # (The rest of your code for this tab...)
        st.header("Descriptive Statistics")
        query_params_for_desc_tab = {"include_columns": effective_cols, "exclude_columns": []}
        
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
                    if title == "Frequency Table":
                        if not effective_categorical_cols: st.info("No categorical columns available.")
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
                        if not effective_categorical_cols: st.info("No categorical columns available.")
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
                    else:
                        with st.spinner(f"Fetching {title}..."):
                            response = requests.get(endpoint_url, params=query_params_for_desc_tab)
                            response.raise_for_status()
                            response_data = response.json()
                            response_type = config.get("response_type")
                            if response_type == "split_df": display_df_from_api_split_response(response_data, f"{title}.")
                            elif response_type == "json_counts": st.json(response_data.get("counts", {}))
                            elif response_type == "text_area_info": st.text_area(f"{title}", response_data.get("info_string", ""), height=300)
                            st.success(f"{title} loaded.")
                except Exception as e:
                    st.error(f"API Error ({title}): {e}")
                    st.session_state[state_var] = False
            st.markdown("---")