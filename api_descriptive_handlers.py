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
    # We need the raw dict.
    cat_columns = des_instance.data.select_dtypes(['object','category']).columns.tolist() # Match original logic
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

    if df_to_process.empty or df_to_process.select_dtypes(include=np.number).empty: # Ensure numpy as np imported
        # Return an empty summary structure if needed by schema
        # This depends on how schemas.DataFrameSplitResponse handles empty data
        # For now, let Descriptive handle it or create an empty describe dict
        temp_des_instance = get_descriptive_instance(df_to_process) # Will work on empty numeric
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

    # Your original handler used: include=["category", "object", "int"]
    # Ensure des_instance.categorical_describe() uses these or a suitable default.
    # If df_to_process is empty, des_instance.categorical_describe() on an empty frame is fine.
    des_instance = get_descriptive_instance(df_to_process)
    summary_df = des_instance.categorical_describe() # Original method uses include=['category', 'object']
                                                     # Adjust if you want 'int' included here too
    return summary_df.to_dict("split")

def handle_data_info_string(
    base_df: pd.DataFrame,
    include_columns: Optional[List[str]] = None,
    exclude_columns: Optional[List[str]] = None
) -> str:
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)
    # Descriptive.data_info() calls df.info() which prints. Capture it.
    des_instance = get_descriptive_instance(df_to_process) # Not strictly needed if we call .info directly
    
    buffer = io.StringIO()
    df_to_process.info(buf=buffer) # Call .info() on the shaped DataFrame
    return buffer.getvalue()

def handle_frequency_table(
    base_df: pd.DataFrame, 
    column_name: str, 
    include_columns: Optional[List[str]], 
    exclude_columns: Optional[List[str]],
    # **kwargs for other crosstab params if needed
) -> Dict[str, Any]: 
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)
    
    if column_name not in df_to_process.columns:
        raise ValueError(f"Column '{column_name}' for frequency table not found in the shaped DataFrame. Available: {df_to_process.columns.tolist()}")
    
    if df_to_process.empty: # Handle case where df might be empty after shaping
        # Return structure for an empty frequency table
        empty_df = pd.DataFrame({'count': []}, index=pd.Index([], name=column_name), dtype=int)
        return {'index': [], 'columns': ['count'], 'data': []} # Manual split dict

    des_instance = get_descriptive_instance(df_to_process)
    # Your original Descriptive.frequency_table had 'column' in error message, ensure it's 'column_name'
    # It also selected cat_data based on ['bool','category','object']. This validation will apply.
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

    # Validate that index_names and columns_names exist in df_to_process
    for name_list_type, name_list_val in [("index_names", index_names), ("columns_names", columns_names)]:
        for name in name_list_val:
            if name not in df_to_process.columns:
                raise ValueError(f"Column '{name}' (from {name_list_type}) not found in shaped DataFrame for crosstabs. Available: {df_to_process.columns.tolist()}")
    
    # Handle if df_to_process becomes empty
    if df_to_process.empty:
         # Construct an empty crosstab-like dictionary structure if possible, or raise error
         # This is tricky as structure depends on index/column names.
         # For now, let Descriptive.cross_tabs handle it or error out.
         print(f"Warning: DataFrame is empty for cross_tabs after shaping.")


    des_instance = get_descriptive_instance(df_to_process)
    try:
        cross_tab_df = des_instance.cross_tabs(
            index_names=index_names, columns_names=columns_names,
            normalize=normalize, margins=margins # Pass any other **kwargs
        )
    except Exception as e: # Catch errors from cross_tabs (e.g., if a column isn't suitable)
        raise ValueError(f"Error generating cross-tabulation on shaped data: {e}")
        
    return cross_tab_df.to_dict("split")

def handle_get_data_filter(
    base_df: pd.DataFrame, 
    filter_cols: List[str], # Changed from 'col' to 'filter_cols' for clarity
    filter_values: List[Any], # Changed from 'value' to 'filter_values'
    include_columns: Optional[List[str]], 
    exclude_columns: Optional[List[str]]
) -> List[Dict[str, Any]]:
    """
    Performs row filtering first, then applies column shaping to the result.
    """
    # 1. Perform row filtering on the base_df
    #    The Descriptive.data_filter method takes Union types, but our API endpoint for this
    #    (using schemas.FilterConditionsRequest) will send lists.
    des_instance_for_filter = get_descriptive_instance(base_df) 
    try:
        row_filtered_df = des_instance_for_filter.data_filter(col=filter_cols, value=filter_values)
    except (ValueError, TypeError) as e: # Catch errors from data_filter itself
        raise # Re-raise as these are likely client input errors (400)
        
    # 2. Then shape the columns of the row_filtered_df
    final_df_to_return = get_shaped_dataframe(row_filtered_df, include_columns, exclude_columns)
    
    return final_df_to_return.to_dict('records')