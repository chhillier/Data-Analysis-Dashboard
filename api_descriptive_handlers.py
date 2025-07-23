import pandas as pd
import io
from typing import Dict, Any, List, Union, Optional
from descriptive import Descriptive
from api_utils import get_shaped_dataframe
import numpy as np
"""
API Handlers for Descriptive Statistics.
These handlers take a base DataFrame, apply column shaping (include/exclude)
and row filtering based on API parameters, then instantiate the Descriptive
class with the processed DataFrame to call its methods and format outputs for the API.
"""
def get_descriptive_instance(df: pd.DataFrame) -> Descriptive:
    return Descriptive(df.copy())

def handle_get_shape(
        base_df: pd.DataFrame,
        include_columns: Optional[List[str]] = None,
        exclude_columns: Optional[List[str]] = None,

) -> Dict[str, int]:
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns,)
    return {"rows" : df_to_process.shape[0], "columns" : df_to_process.shape[1]}


def handle_get_unique_counts(
    base_df: pd.DataFrame,
    include_columns: Optional[List[str]] = None,
    exclude_columns: Optional[List[str]] = None
) -> Dict[str, int]:
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)
    
    # Handle empty DataFrame after shaping
    if df_to_process.empty:
        return {}

    des_instance = get_descriptive_instance(df_to_process)
    # Original Descriptive.check_unique_counts returns a formatted string.
    cat_columns = des_instance.data.select_dtypes(['object','category']).columns.tolist()
    if not cat_columns:
        return {}
    unique_counts = des_instance.data[cat_columns].nunique()
    return unique_counts.to_dict()

def handle_numerical_summary(
    base_df: pd.DataFrame, 
    precision: int = 2,
    include_columns: Optional[List[str]] = None,
    exclude_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)

    if df_to_process.empty or df_to_process.select_dtypes(include=np.number).empty:
        temp_des_instance = get_descriptive_instance(df_to_process)
        return temp_des_instance.numerical_describe(precision=precision).to_dict("split")


    des_instance = get_descriptive_instance(df_to_process)
    summary_df = des_instance.numerical_describe(precision=precision)
    return summary_df.to_dict("split")

def handle_categorical_summary(
    base_df: pd.DataFrame,
    include_columns: Optional[List[str]] = None,
    exclude_columns: Optional[List[str]] = None
) -> Dict[str,Any]:
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)

    des_instance = get_descriptive_instance(df_to_process)
    summary_df = des_instance.categorical_describe()
                                                     
    return summary_df.to_dict("split")

def handle_data_info_string(
    base_df: pd.DataFrame,
    include_columns: Optional[List[str]] = None,
    exclude_columns: Optional[List[str]] = None
) -> str:
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)
    des_instance = get_descriptive_instance(df_to_process)
    
    buffer = io.StringIO()
    df_to_process.info(buf=buffer)
    return buffer.getvalue()

def handle_frequency_table(
    base_df: pd.DataFrame, 
    column_name: str, 
    include_columns: Optional[List[str]], 
    exclude_columns: Optional[List[str]],

) -> Dict[str, Any]: 
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)
    
    if column_name not in df_to_process.columns:
        raise ValueError(f"Column '{column_name}' for frequency table not found in the shaped DataFrame. Available: {df_to_process.columns.tolist()}")
    
    if df_to_process.empty: 
        empty_df = pd.DataFrame({'count': []}, index=pd.Index([], name=column_name), dtype=int)
        return {'index': [], 'columns': ['count'], 'data': []} # Manual split dict

    des_instance = get_descriptive_instance(df_to_process)
    try:
        freq_table_df = des_instance.frequency_table(column_name=column_name) # Pass any other **kwargs
    except ValueError as e: # Catch errors from frequency_table itself
        raise ValueError(f"Error generating frequency table for '{column_name}' on shaped data: {e}")
        
    return freq_table_df.to_dict("split")

def handle_cross_tabs(
    base_df: pd.DataFrame, 
    index_names: List[str], 
    columns_names: List[str],
    include_columns: Optional[List[str]], 
    exclude_columns: Optional[List[str]],
    normalize: bool = False, 
    margins: bool = False
    # **kwargs for other crosstab params if needed
) -> Dict[str, Any]:
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)
    for name_list_type, name_list_val in [("index_names", index_names), ("columns_names", columns_names)]:
        for name in name_list_val:
            if name not in df_to_process.columns:
                raise ValueError(f"Column '{name}' (from {name_list_type}) not found in shaped DataFrame for crosstabs. Available: {df_to_process.columns.tolist()}")
    
    # Handle if df_to_process becomes empty
    if df_to_process.empty:
         print(f"Warning: DataFrame is empty for cross_tabs after shaping.")


    des_instance = get_descriptive_instance(df_to_process)
    try:
        cross_tab_df = des_instance.cross_tabs(
            index_names=index_names, columns_names=columns_names,
            normalize=normalize, margins=margins # Pass any other **kwargs
        )
    except Exception as e: # Catch errors from cross_tabs (e.g., if a column isn't suitable)
        raise ValueError(f"Error generating cross-tabulation on shaped data: {e}")
    
    # --- Flatten MultiIndex columns if they exist ---
    if isinstance(cross_tab_df.columns, pd.MultiIndex):
        cross_tab_df.columns = ['_'.join(map(str, col_level)).strip('_') for col_level in cross_tab_df.columns.values]
        
    return cross_tab_df.to_dict("split")

def handle_get_data_filter(
    base_df: pd.DataFrame, 
    filter_cols: List[str],
    filter_values: List[Any],
    include_columns: Optional[List[str]], 
    exclude_columns: Optional[List[str]]
) -> List[Dict[str, Any]]:
    """
    Performs row filtering first, then applies column shaping to the result.
    """
   
    des_instance_for_filter = get_descriptive_instance(base_df) 
    try:
        row_filtered_df = des_instance_for_filter.data_filter(col=filter_cols, value=filter_values)
    except (ValueError, TypeError) as e: # Catch errors from data_filter itself
        raise # Re-raise as these are likely client input errors (400)
        
    # 2. Then shape the columns of the row_filtered_df
    final_df_to_return = get_shaped_dataframe(row_filtered_df, include_columns, exclude_columns)
    
    return final_df_to_return.to_dict('records')