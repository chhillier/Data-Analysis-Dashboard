# dashboard.py (Corrected Try-Except Blocks and Plot Generator)
import streamlit as st
import requests 
import pandas as pd 
from typing import List, Dict, Any, Optional, Union # Ensure Union is imported for PlotParameter use later
import traceback # For more detailed error printing in Streamlit console

# --- Configuration ---
FASTAPI_BASE_URL = "http://localhost:8000/api" 

st.set_page_config(layout="wide", page_title="Data Analysis Dashboard")
st.title("📊 Data Analysis Dashboard")

# --- Cached Function to Fetch Column Names ---
@st.cache_data(ttl=600) 
def get_column_data_from_api() -> Optional[Dict[str, List[str]]]:
    """Fetches all, categorical, and numerical column names from the API."""
    columns_endpoint = f"{FASTAPI_BASE_URL}/data/columns"
    print(f"DEBUG dashboard.py: Calling get_column_data_from_api() (API call if not cached)...")
    try:
        response = requests.get(columns_endpoint)
        response.raise_for_status() 
        data = response.json()
        print(f"DEBUG dashboard.py: get_column_data_from_api returned: {data}")
        return data
    except requests.exceptions.HTTPError as e_http:
        st.error(f"API Error fetching columns: Status {e_http.response.status_code}")
        try:
            error_detail = e_http.response.json()
            st.json(error_detail.get("detail", error_detail))
        except ValueError: # If response is not JSON
            st.text_area("Raw API error response:", e_http.response.text, height=100)
        return None
    except requests.exceptions.RequestException as e_req:
        st.error(f"Connection Error fetching columns: Could not reach API. {e_req}")
        return None
    except Exception as e_gen:
        st.error(f"An unexpected error occurred while fetching column data: {e_gen}")
        return None

# --- Initialize Session State (Columns and UI Toggles) ---
if 'app_initialized' not in st.session_state:
    st.warning("Initializing application state (columns and UI toggles)...") 
    column_data = get_column_data_from_api() 
    default_fallback_cols = ["select_column", "fallback_A", "fallback_B", "fallback_C"] 

    if column_data:
        st.session_state.all_columns = column_data.get("all_columns", default_fallback_cols)
        st.session_state.numerical_cols = column_data.get("numerical_columns", [default_fallback_cols[0]] if default_fallback_cols else [])
        st.session_state.categorical_cols = column_data.get("categorical_columns", [default_fallback_cols[1]] if len(default_fallback_cols) > 1 else [])
        if not st.session_state.all_columns: 
            st.warning("Column data from API was empty. Using fallback names in session state.")
            st.session_state.all_columns = default_fallback_cols
            st.session_state.numerical_cols = [default_fallback_cols[0]] if default_fallback_cols else []
            st.session_state.categorical_cols = [default_fallback_cols[1]] if len(default_fallback_cols) > 1 else []
    else: 
        st.warning("API for columns failed. Using fallback column names in session state.")
        st.session_state.all_columns = default_fallback_cols
        st.session_state.numerical_cols = [default_fallback_cols[0]] if default_fallback_cols else []
        st.session_state.categorical_cols = [default_fallback_cols[1]] if len(default_fallback_cols) > 1 else []
    
    st.session_state.show_numerical_summary = False
    st.session_state.show_categorical_summary = False
    st.session_state.show_unique_counts = False 
    st.session_state.show_frequency_table_section = False # For section visibility
    st.session_state.show_crosstab_section = False      # For section visibility
    st.session_state.show_dataset_shape = False
    st.session_state.show_dataset_info = False
    st.session_state.show_filtered_data_view = False
    
    st.session_state.app_initialized = True
    st.rerun()

all_columns: List[str] = st.session_state.get('all_columns', [])
numerical_cols: List[str] = st.session_state.get('numerical_cols', [])
categorical_cols: List[str] = st.session_state.get('categorical_cols', [])

st.sidebar.title("Controls & Options") 

tab_plots, tab_descriptive_stats, tab_data_view = st.tabs([
    "📊 Plot Dashboard", 
    "🔢 Descriptive Statistics", 
    "📄 View/Filter Data"
])

def display_df_from_api_split_response(
    response_data_split: Dict[str, Any], 
    success_message: str = "Data loaded.", 
    index_level_names: Optional[List[str]] = None
):
    print(f"\n--- DEBUG dashboard.py: display_df_from_api_split_response for {success_message} ---") 
    index_from_json = response_data_split.get('index', [])
    columns_from_json = response_data_split.get('columns', [])
    data_from_json = response_data_split.get('data', [])
    # ... (rest of debug prints from previous full version of this helper) ...

    if (response_data_split and data_from_json is not None and 
        columns_from_json is not None and index_from_json is not None):
        try:
            reconstructed_index = None
            if index_from_json: 
                processed_index_tuples = [tuple(item) if isinstance(item, list) else item for item in index_from_json]
                if processed_index_tuples and isinstance(processed_index_tuples[0], tuple): 
                    reconstructed_index = pd.MultiIndex.from_tuples(processed_index_tuples, names=index_level_names)
                elif processed_index_tuples: 
                    idx_name_for_single = None
                    if index_level_names and isinstance(index_level_names, list) and len(index_level_names) == 1: idx_name_for_single = index_level_names[0]
                    elif isinstance(index_level_names, str): idx_name_for_single = index_level_names
                    reconstructed_index = pd.Index(processed_index_tuples, name=idx_name_for_single)
            elif not data_from_json : reconstructed_index = pd.Index([])
            df_display = pd.DataFrame(data=data_from_json, index=reconstructed_index, columns=columns_from_json)
            cols_to_stringify = [col for col in st.session_state.get('categorical_cols', []) if col in df_display.columns]
            if cols_to_stringify:
                for col_name_to_str in cols_to_stringify:
                    try: 
                        if not df_display[col_name_to_str].empty: df_display[col_name_to_str] = df_display[col_name_to_str].astype(str)
                    except Exception as e_astype: print(f"DEBUG: Could not convert column '{col_name_to_str}' to string: {e_astype}")
            st.dataframe(df_display)
            st.success(success_message)
        except ValueError as ve: 
            st.error(f"Pandas Error creating/processing DataFrame: {ve}")
            print(f"--- PANDAS DataFrame CREATION ValueError (Streamlit Console) ---"); traceback.print_exc()
        except Exception as ex_df_create: 
            st.error(f"Unexpected error creating DataFrame: {ex_df_create}"); print(f"--- UNEXPECTED DataFrame CREATION Error ---"); traceback.print_exc()
    else: st.warning("Data for table incomplete or not in 'split' format.")

# --- Tab 1: Plot Dashboard ---
with tab_plots:
    st.header("Plot Generation")
    with st.expander("Plot Controls", expanded=True):
        st.subheader("Column Selection for Plot (applies to generated plot below)")
        plot_tab_include_cols = st.multiselect("Include columns:", st.session_state.get('all_columns', []), default=None, key="plot_tab_include_main_v3")
        plot_tab_exclude_cols = st.multiselect("Exclude columns:", st.session_state.get('all_columns', []), default=None, key="plot_tab_exclude_main_v3")
        st.markdown("---")
        st.subheader("Configure and Generate Single Plot")
        
        plot_types_available = ["histogram", "kde", "scatter", "bar_chart", "count_plot", "crosstab_heatmap", "displot"]
        selected_plot_type = st.selectbox("Select Plot Type:", plot_types_available, key="plot_type_select_main_v3")
        
        # Initialize plot_params_ui for the selected type
        plot_params_ui = {}
        
        #--- Conditionally display Primary Column ---
        #Used by most plots except crosstab_heatmap
        if selected_plot_type is not "crosstab_heatmap":
            plot_params_ui['col_name'] = st.selectbox("Primary Column (col_name/x_col):", [None] + st.session_state.get('all_columns',[]), 
                                                  index=0 , 
                                                  key="plot_param_col_name_main_v3")
        #--- Conditionally display Hue Column ---
        #Used by kde, scatter, bar chart, count plot, displot. Not used by histogram or crosstab_heatmap
        if selected_plot_type in ["kde", "scatter", "bar_chart", "count_plot", "displot"]:
            plot_params_ui['hue_col'] = st.selectbox("Hue Column (hue_col):", [None] + st.session_state.get('categorical_cols',[]), 
                                                index=0,
                                                key="plot_param_hue_col_main_v3")    
        
        # Conditional UI for specific plot parameters
        if selected_plot_type == "histogram":
            plot_params_ui['bins'] = st.slider("Bins:", 10, 100, 30, key="hist_bins_main_v3")
            plot_params_ui['kde'] = st.checkbox("Overlay KDE?", value=False, key="hist_kde_main_v3")

            if plot_params_ui['kde']:
                default_kde_color = "#FF5733"
                current_bar_color = plot_params_ui.get('color', "#1f77b4").lower()
                if current_bar_color == default_kde_color.lower():
                    default_kde_color = "#33FF57"
                plot_params_ui['kde_line_collor'] = st.color_picker(
                    "KDE Line Color:",
                    default_kde_color,
                    key = "hist_kde_line_color_main_v3"
                )
            plot_params_ui['color'] = st.color_picker("Bar Color", "#1f77b4", key="hist_color_main_v3") # Default matplotlib blue
            user_edgecolor = st.text_input("Edge Color (e.g., black or None):", "None", key="hist_edge_main_v3")
            if not user_edgecolor or user_edgecolor.strip().lower() == 'none':
                plot_params_ui['edgecolor'] = None
            else:
                plot_params_ui['edgecolor'] = user_edgecolor
            plot_params_ui['stat'] = st.selectbox("Statistic:", ["count", "frequency", "density", "probability"], index=0, key="hist_stat_main_v3")

        elif selected_plot_type == "kde":
            plot_params_ui['fill'] = st.checkbox("Fill KDE plot?", value=True, key="kde_fill_main_v3")
            plot_params_ui['alpha'] = st.slider("Alpha (transparency):", 0.0, 1.0, 0.7, key="kde_alpha_main_v3")
            plot_params_ui['linewidth'] = st.slider("Line Width:", 0.5, 5.0, 1.5, step=0.5, key="kde_linewidth_main_v3")
        
        elif selected_plot_type == "scatter":
            x_axis_column_choice = plot_params_ui.pop('col_name', None)
            if x_axis_column_choice:
                plot_params_ui['col_name_x'] = x_axis_column_choice
            y_axis_column_choice = st.selectbox(
                "Y-axis Column:",
                options = [None] + st.session_state.get('numerical_cols', []),
                index = 0,
                key = "scatter_y_main_v3",
            )
            if y_axis_column_choice:
                plot_params_ui['col_name_y'] = y_axis_column_choice
            plot_params_ui["alpha"] = st.slider(
                "Point Transparency (Alpha, 0=invisible, 1=solid):",
                min_value=0.0, max_value=1.0,
                value=0.5,
                key="scatter_alpha_main_v3"
            )
            plot_params_ui['s'] = st.slider(
                "Point Size (s):",
                min_value = 10, max_value = 200,
                value = 50,
                key="scatter_s_main_v3"
            )
        
        elif selected_plot_type == "bar_chart":
            primary_column_for_x = plot_params_ui.pop('col_name', None)
            if primary_column_for_x:
                plot_params_ui['x_col'] = primary_column_for_x

            y_axis_column_choice = st.selectbox(
                "Y-axis Column (determines bar height, numerical): ",
                options = [None] + st.session_state.get('numerical_cols', [],
                                                       ),
                index = 0,
                key = "bar_y_main_v3"
            )
            if y_axis_column_choice:
                plot_params_ui['y_col'] = y_axis_column_choice

            estimator_options = [None, 'mean', 'median', 'sum']
            estimator_choice = st.selectbox(
                "Estimator (if Y column is chosen, how to aggregate it):",
                options = estimator_options,
                index = 0,
                key = "bar_estimator_main_v3"
            )
            if estimator_choice:
                plot_params_ui['estimator'] = estimator_choice

            errorbar_options = [None, "sd", "ci", "se", "pi"]
            errorbar_choice = st.selectbox(
                "Error Bars (show uncertainty on bar height):",
                options = errorbar_options,
                index= 0,
                key = "bar_errorbar_main_v3"
            )
            if errorbar_choice:
                plot_params_ui['errorbar'] = errorbar_choice
            user_palette_bar = st.text_input(
                "Color Palette (optional, e.g., 'viridis', 'pastel'):",
                value = "",
                key = "bar_palette_main_v3"
            )
            if user_palette_bar.strip():
                plot_params_ui['palette'] = user_palette_bar.strip()

        elif selected_plot_type == "count_plot":
            primary_column_for_x = plot_params_ui.pop('col_name', None)
            if primary_column_for_x:
                plot_params_ui['x_col'] = primary_column_for_x

            plot_params_ui['dodge'] = st.checkbox(
                "Separate bars by hue (dodge)?",
                value= True,
                key = "count_dodge_main_v3"
            )

            user_palette_count = st.text_input(
                "Color Palette (optional, e.g., 'pastel', 'Set2'):",
                value="",
                key = "count_palette_main_v3"
            )
            if user_palette_count.strip():
                plot_params_ui['palette'] = user_palette_count.strip()

        elif selected_plot_type == "crosstab_heatmap":
            index_cols_selection = st.multiselect(
                "Select Index Column(s) (for heatmap rows):",
                options = st.session_state.get('categorical_cols', []),
                default= [],
                key = "heatmap_idx_main_v3"
            )
            if index_cols_selection:
                plot_params_ui['index_names_ct'] = index_cols_selection

            column_cols_selection = st.multiselect(
                "Select Column(s) (for heatmap columns):",
                options = st.session_state.get('categorical_cols', []),
                default= [],
                key = "heatmap_col_main_v3"

            )
            if column_cols_selection:
                plot_params_ui['column_names_ct'] = column_cols_selection

            plot_params_ui['annot'] = st.checkbox(
                "Show values on heatmap cells (annotate)?",
                value = True,
                key = "heatmap_annot_main_v3"
            )

            user_annotation_format = st.text_input(
                "Format for cell values (if annotating, e.g., '.0f' for no decimals, 'd' for integer):",
                value = ".0f",
                key = "heatmap_fmt_main_v3"
            )
            if user_annotation_format.strip():
                plot_params_ui['fmt'] = user_annotation_format.strip()

            user_colormap = st.text_input(
                "Color scheme (cmap, e.g., 'YlGnBu', 'viridis', 'coolwarm'):",
                value = "YlGnBu",
                key = "heatmap_cmap_main_v3"

            )
            if user_colormap.strip():
                plot_params_ui['cmap'] = user_colormap.strip()

        
        elif selected_plot_type == "displot":
            displot_kind_options = ["hist", "kde", "ecdf"]
            plot_params_ui['kind'] = st.selectbox(
                "Kind of Distribution Plot:",
                options = displot_kind_options,
                index = 0,
                key = "displot_param_kind_main_v3"
            )


        if st.button(f"Generate {selected_plot_type}", key=f"gen_dyn_plot_main_v3"):
            ready_to_plot = False
            # Validate essential parameters based on plot type
            if selected_plot_type in ["histogram", "kde", "displot"] and plot_params_ui.get('col_name'):
                ready_to_plot = True
            elif selected_plot_type == "scatter" and plot_params_ui.get('col_name_x') and plot_params_ui.get('col_name_y'):
                ready_to_plot = True
            elif selected_plot_type in ["bar_chart", "count_plot"] and plot_params_ui.get('x_col'):
                ready_to_plot = True
            elif selected_plot_type == "crosstab_heatmap" and plot_params_ui.get('index_names_ct') and plot_params_ui.get('column_names_ct'):
                ready_to_plot = True
            
            if ready_to_plot:
                final_plot_params = {k: v for k, v in plot_params_ui.items() if v is not None or k in ['fill','annot','kde','cbar','dodge']} # Keep bools even if False
                # Ensure correct mapping for x_col if col_name was used
                
                dynamic_plot_config = [{"type": selected_plot_type, "params": final_plot_params}]
                endpoint_url = f"{FASTAPI_BASE_URL}/plots/dashboard"
                query_params_plots = {}
                if plot_tab_include_cols: query_params_plots["include_columns"] = plot_tab_include_cols
                if plot_tab_exclude_cols: query_params_plots["exclude_columns"] = plot_tab_exclude_cols
                st.info(f"Requesting dynamic plot: {selected_plot_type} ...")
                try:
                    with st.spinner(f"Generating {selected_plot_type}..."):
                        response = requests.post(endpoint_url, json=dynamic_plot_config, params=query_params_plots) 
                    response.raise_for_status()
                    st.image(response.content, caption=f"Generated {selected_plot_type}", use_container_width=True)
                except requests.exceptions.HTTPError as e_http:
                    st.error(f"API Error (Dynamic Plot): Status {e_http.response.status_code}")
                    try: st.json(e_http.response.json().get("detail", e_http.response.json()))
                    except: st.text_area("Raw API error:", e_http.response.text, height=200)
                except requests.exceptions.RequestException as e_req: st.error(f"Connection error: {e_req}")
                except Exception as e_gen: st.error(f"Unexpected error: {e_gen}")
            else: st.warning("Please select all necessary columns/parameters for the chosen plot type.")

# --- Tab 2: Descriptive Statistics (All sections toggleable) ---
with tab_descriptive_stats:
    st.header("Descriptive Statistics")
    with st.sidebar.expander("Descriptive Statistics Controls", expanded=True):
        st.subheader("Column Selection for Statistics")
        desc_include_cols = st.multiselect("Include columns for statistics:", st.session_state.get('all_columns', []), default=None, key="desc_include_final_v3")
        desc_exclude_cols = st.multiselect("Exclude columns for statistics:", st.session_state.get('all_columns', []), default=None, key="desc_exclude_final_v3")

    query_params_for_desc_tab = {}
    if desc_include_cols: query_params_for_desc_tab["include_columns"] = desc_include_cols
    if desc_exclude_cols: query_params_for_desc_tab["exclude_columns"] = desc_exclude_cols

    sections = {
        "Numerical Summary": {"endpoint": "numerical-summary", "state_var": "show_numerical_summary", "key_suffix": "num_sum_v4", "response_type": "split_df", "params_func": lambda: query_params_for_desc_tab},
        "Categorical Summary": {"endpoint": "categorical-summary", "state_var": "show_categorical_summary", "key_suffix": "cat_sum_v4", "response_type": "split_df", "params_func": lambda: query_params_for_desc_tab},
        "Unique Value Counts": {"endpoint": "unique-counts", "state_var": "show_unique_counts", "key_suffix": "unique_v4", "response_type": "json_counts", "params_func": lambda: query_params_for_desc_tab},
        "Dataset Shape": {"endpoint": "shape", "state_var": "show_dataset_shape", "key_suffix": "shape_v4", "response_type": "json_direct", "params_func": lambda: query_params_for_desc_tab},
        "Dataset Info": {"endpoint": "info", "state_var": "show_dataset_info", "key_suffix": "info_v4", "response_type": "text_area_info", "params_func": lambda: query_params_for_desc_tab}
    }

    for title, config in sections.items():
        st.subheader(title)
        button_label = f"Hide {title}" if st.session_state.get(config["state_var"], False) else f"Show {title}"
        if st.button(button_label, key=f"btn_toggle_{config['key_suffix']}"):
            st.session_state[config["state_var"]] = not st.session_state.get(config["state_var"], False)
            st.rerun()
        
        if st.session_state.get(config["state_var"], False):
            endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/{config['endpoint']}"
            api_params = config["params_func"]() # Gets query_params_for_desc_tab
            # Add specific params for numerical_summary precision if UI exists
            if title == "Numerical Summary":
                 # precision_val = st.sidebar.slider("Precision", 0, 5, 2, key="num_sum_precision") # Example UI
                 # api_params["precision"] = precision_val
                 pass # For now, uses API default precision

            st.info(f"Requesting {title} with params: {api_params}")
            try:
                with st.spinner(f"Fetching {title.lower()}..."):
                    response = requests.get(endpoint_url, params=api_params)
                response.raise_for_status()
                if config["response_type"] == "split_df":
                    display_df_from_api_split_response(response.json(), f"{title}.")
                elif config["response_type"] == "json_counts":
                    data = response.json();
                    if data and "counts" in data: st.json(data["counts"]); st.success(f"{title} loaded.")
                    else: st.warning(f"{title} data not in expected format."); st.json(data)
                elif config["response_type"] == "json_direct":
                    st.json(response.json()); st.success(f"{title} loaded.")
                elif config["response_type"] == "text_area_info":
                    data = response.json()
                    st.text_area(f"{title}", data.get("info_string", "No info available."), height=300); st.success(f"{title} loaded.")
            except requests.exceptions.HTTPError as e_http:
                st.error(f"API Error ({title}): Status {e_http.response.status_code}")
                try: st.json(e_http.response.json().get("detail", e_http.response.json()))
                except: st.text_area("Raw API error:", e_http.response.text, height=100)
                st.session_state[config["state_var"]] = False; st.rerun()
            except requests.exceptions.RequestException as e_req:
                st.error(f"Connection Error ({title}): {e_req}"); st.session_state[config["state_var"]] = False; st.rerun()
            except Exception as e_gen: 
                st.error(f"Error ({title}): {e_gen}"); print(f"--- Error ({title}) ---"); traceback.print_exc(); print(f"---")
                st.session_state[config["state_var"]] = False; st.rerun()
        st.markdown("---")

    # Frequency Table (Toggleable Section and then Generate Button)
    st.subheader("Frequency Table")
    freq_table_label = "Hide Frequency Table Section" if st.session_state.get('show_frequency_table_section', False) else "Show Frequency Table Section"
    if st.button(freq_table_label, key="btn_toggle_freq_table_section_v3"):
        st.session_state.show_frequency_table_section = not st.session_state.get('show_frequency_table_section', False)
        st.rerun()

    if st.session_state.get('show_frequency_table_section', False):
        if not st.session_state.get('categorical_cols'):
            st.info("Categorical columns not yet loaded or none available.")
        else:
            selected_col_freq = st.selectbox("Select column for frequency table:", st.session_state.categorical_cols, 
                                             index=st.session_state.categorical_cols.index("cut") if "cut" in st.session_state.categorical_cols else 0, 
                                             key="freq_table_col_select_v4")
            if st.button("Generate Frequency Table", key="btn_gen_freq_table_v4"):
                endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/frequency-table"
                current_q_params = query_params_for_desc_tab.copy()
                current_q_params["column_name"] = selected_col_freq
                st.info(f"Requesting Frequency Table for '{selected_col_freq}' with params: {current_q_params}")
                try:
                    with st.spinner(f"Fetching frequency table..."):
                        response = requests.get(endpoint_url, params=current_q_params)
                    response.raise_for_status()
                    display_df_from_api_split_response(response.json(), f"Frequency table for '{selected_col_freq}'.", index_level_names=[selected_col_freq])
                except requests.exceptions.HTTPError as e_http: 
                    st.error(f"API Error (Freq Table): Status {e_http.response.status_code}")
                    try: st.json(e_http.response.json().get("detail", e_http.response.json()))
                    except: st.text_area("Raw API error:", e_http.response.text, height=100)
                except requests.exceptions.RequestException as e_req: st.error(f"Connection Error (Freq Table): {e_req}")
                except Exception as e_gen: st.error(f"Error (Freq Table): {e_gen}"); print(f"--- Error (Freq Table) ---"); traceback.print_exc()
    st.markdown("---")

    # Cross-Tabulations (Toggleable Section and then Generate Button)
    st.subheader("Cross-Tabulations")
    crosstab_label = "Hide Cross-Tabulation Section" if st.session_state.get('show_crosstab_section', False) else "Show Cross-Tabulation Section"
    if st.button(crosstab_label, key="btn_toggle_crosstab_section_v3"):
        st.session_state.show_crosstab_section = not st.session_state.get('show_crosstab_section', False)
        st.rerun()

    if st.session_state.get('show_crosstab_section', False):
        if not st.session_state.get('categorical_cols') or len(st.session_state.get('categorical_cols', [])) < 1 :
            st.info("Not enough categorical columns loaded or available for cross-tabulation.")
        else:

            index_name_crosstab_select = st.multiselect("Select index column(s) for Crosstab:", st.session_state.categorical_cols, default=[], key="crosstab_index_v4")
            column_name_crosstab_select = st.multiselect("Select column(s) for Crosstab:", st.session_state.categorical_cols, default=[], key="crosstab_columns_v4")
            crosstab_normalize = st.checkbox("Normalize Crosstab?", value=False, key="crosstab_normalize_v4")
            crosstab_margins = st.checkbox("Show Crosstab Margins?", value=False, key="crosstab_margins_v4")

            if st.button("Generate Cross-Tabulation Table", key="btn_gen_crosstab_table_v3"):
                if not index_name_crosstab_select or not column_name_crosstab_select:
                    st.warning("Please select at least one index AND one column for cross-tabulation.")
                else:
                    endpoint_url = f"{FASTAPI_BASE_URL}/descriptive/cross-tabs" 
                    payload = {
                        "index_names": index_name_crosstab_select,
                        "column_names": column_name_crosstab_select, 
                        "normalize": crosstab_normalize,
                        "margins": crosstab_margins
                    }
                    try:
                        with st.spinner("Generating cross-tabulation..."):
                            response = requests.post(endpoint_url, json=payload, params=query_params_for_desc_tab)
                        response.raise_for_status() 
                        display_df_from_api_split_response(response.json(), "Cross-tabulation loaded.", index_level_names=index_name_crosstab_select)
                    except requests.exceptions.HTTPError as e_http: 
                        st.error(f"API Error (Crosstab): Status {e_http.response.status_code}")
                        try: st.json(e_http.response.json().get("detail", e_http.response.json()))
                        except: st.text_area("Raw API error:", e_http.response.text, height=200)
                    except requests.exceptions.RequestException as e_req: st.error(f"Connection Error (Crosstab): {e_req}")
                    except Exception as e_gen: 
                        st.error(f"Error (Crosstab): {e_gen}"); print(f"--- Error (Crosstab) ---"); traceback.print_exc()
    st.markdown("---")


# --- Tab 3: View/Filter Data ---
with tab_data_view:
    st.header("View and Filter Data Subset")
    with st.sidebar.expander("Data View & Filter Controls", expanded=True):
        st.subheader("Row Filters")
        filter_col_select = st.selectbox("Filter by column:", [None] + st.session_state.get('all_columns',[]), index=0, key="filter_col_select_view_v3")
        filter_value_input = "" 
        if filter_col_select:
            filter_value_input = st.text_input(f"Enter value to filter for in '{filter_col_select}':", key="filter_value_input_view_v3")
        st.subheader("Column Selection for View")
        view_tab_include_cols_default = st.session_state.get('all_columns', [])
        view_tab_include_cols = st.multiselect("Include columns in view:", st.session_state.get('all_columns',[]), default=view_tab_include_cols_default, key="view_tab_include_v3")
        view_tab_exclude_cols = st.multiselect("Exclude columns from view:", st.session_state.get('all_columns',[]), default=None, key="view_tab_exclude_v3")

    filter_data_label = "Hide Filtered Data" if st.session_state.get('show_filtered_data_view', False) else "Show Filtered/Shaped Data"
    if st.button(filter_data_label, key="btn_toggle_filtered_data_v3"): # Incremented key
        st.session_state.show_filtered_data_view = not st.session_state.get('show_filtered_data_view', False)
        st.rerun()

    if st.session_state.get('show_filtered_data_view', False):
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
        except requests.exceptions.HTTPError as e_http:
            st.error(f"API Error (Filtered Data): Status {e_http.response.status_code}")
            try: st.json(e_http.response.json().get("detail", e_http.response.json()))
            except: st.text_area("Raw API error:", e_http.response.text, height=200)
            st.session_state.show_filtered_data_view = False; st.rerun()
        except requests.exceptions.RequestException as e_req: 
            st.error(f"Connection Error (Filtered Data): {e_req}"); st.session_state.show_filtered_data_view = False; st.rerun()
        except Exception as e_gen: 
            st.error(f"Error processing filtered data: {e_gen}")
            print(f"--- Error processing filtered data (Streamlit Console) ---"); traceback.print_exc(); print(f"---")
            st.session_state.show_filtered_data_view = False; st.rerun()