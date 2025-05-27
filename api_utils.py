import pandas as pd
from typing import List, Optional

def get_shaped_dataframe(
        base_df : pd.DataFrame,
        include_columns: Optional[List[str]] = None,
        exclude_columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Applies column inclusion or exclusion to a DataFrame based on API parameters
    - IF include_colmns is provided, only these columns are kept. It takes priority
    - ELSE IF excludes_columns is provided, these columns are dropped.
    - Returns a new shaped DataFrame
    """
    current_df = base_df.copy()

    if include_columns is not None:
        #Filter include_columns to only those that actually exist in current_df
        valid_include_cols = [col for col in include_columns if col in current_df.columns]

        if not valid_include_cols:
            if include_columns:
                print(f"Warning: None of the specified include_columns {include_columns} exist in the DataFrame. "
                      "Returning DataFrame with no columns as per include request. ")
                return pd.DataFrame(columns=include_columns)
        else:
            current_df = current_df[valid_include_cols]
    
    elif exclude_columns is not None:
        valid_exclude_cols = [col for col in exclude_columns if col in current_df.columns]
        if valid_exclude_cols:

            current_df = current_df.drop(columns=valid_exclude_cols)
        elif exclude_columns:
            print(f"Warning: None of the specified exclude_columns {exclude_columns} exist to be dropped. No columns to be removed. ")
            

    return current_df

