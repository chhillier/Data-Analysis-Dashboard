import pandas as pd
import io
from typing import Dict, Any, List
from descriptive import Descriptive
import seaborn as sns
"""

des_instance : Descriptive is making an instance of
Descriptive use that to call methods from it

"""
def get_descriptive_instance(df: pd.DataFrame) -> Descriptive:
    return Descriptive(df.copy())

def handle_get_shape(des_instance: Descriptive) -> Dict[str, int]:
    return {"rows": des_instance.data.shape[0], "columns": des_instance.data.shape[1]}

def handle_get_unique_counts(des_instance: Descriptive) -> Dict[str, int]:
    cat_columns = des_instance.data.select_dtypes(['category', 'int', 'object']).columns.tolist()
    if not cat_columns:
        return {}
    unique_counts = des_instance.data[cat_columns].nunique()
    return unique_counts.to_dict()

def handle_numerical_summary(des_instance: Descriptive, precision: int = 2) -> Dict[str, Any]:
    summary_df = des_instance.numerical_describe(precision=precision)
    return summary_df.to_dict("split")

def handle_categorical_summary(des_instance: Descriptive) -> Dict[str,Any]:
    summary_df = des_instance.categorical_describe(include=["category", "object", "int"])
    return summary_df.to_dict("split")

def handle_data_info_string(des_instance: Descriptive) -> str:
    """
    Captures the output of the DataFrame's info() method to a string
    Relies on Descriptive.data_info() or directly calls info() on the DataFrame.
    """
    buffer = io.StringIO()
    des_instance.data.info(buf=buffer)
    return buffer.getvalue()

def handle_frequency_table(des_instance: Descriptive, column_name: str, **kwargs) -> Dict[str, Any]:
    """
    Calls the frequency_table method
    Validates column_name and converts the resulting DataFrame to 'split' dict format
    """
    if column_name not in des_instance.data.columns:
        raise ValueError(f"Column '{column_name}' not found in DataFrame for frequency table")
    
    freq_table_df = des_instance.frequency_table(column=column_name, **kwargs)
    return freq_table_df.to_dict("split")

def handle_cross_tabs(des_instance: Descriptive, index_names: List[str], columns_names: List[str],
                      normalize: bool = False, margins: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Calls the cross_tabs method.
    Performs basic validation on column names and converts the resulting Dataframe to 'split' dict format
    """

    for name_list in [index_names, columns_names]:
        for name in name_list:
            if name not in des_instance.data.columns:
                raise ValueError(f"Column '{name}' not found in DataFrame for crosstabs")
            
    cross_tab_df = des_instance.cross_tabs(index_names=index_names, columns_names=columns_names,
                                           normalize=normalize, margins=margins, **kwargs)
    return cross_tab_df.to_dict("split")

def handle_get_data_filter(des_instance: Descriptive, col: str, cat: str) -> List[Dict[str, Any]]:
    """
    Calls the data_filter method
    Converts the resulting filtered DataFrame to a list of records (dictionaries).
    """
    filtered_df = des_instance.data_filter(col=col,cat=cat)
    return filtered_df.to_dict('records')



