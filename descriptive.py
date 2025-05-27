import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Optional, Union, Any

# df = sns.load_dataset('diamonds')
# print(df.head())
# print(df['cut'].nunique())
# print(df['clarity'].nunique())

class Descriptive:
    def __init__(self,data):
        self.data = data
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a pandas DF")
    def check_unique_counts(self):
        cat = self.data.select_dtypes(['object','category']).columns.tolist()
        counts = self.data[cat].nunique()
        return f"\nThese are the unique counts for each category : {counts.to_dict()} \n"
    def check_rows_and_columns_counts(self):
        return f"Has {self.data.shape[0]} rows and {self.data.shape[1]} columns \n"
    def numerical_describe(self,precision=2):
        return self.data.describe(include='number').round(precision)
    def categorical_describe(self):
        return self.data.describe(include=['category', 'object'])
    def data_info(self):
        return self.data.info()
    def data_filter(self, col: Union[str, List[str]], value: Union[Any, List[Any]]) -> pd.DataFrame:
        """
        Filters the DataFrame.
        - If col is a string and value is a single item: filters by that single condition.
        - If col is a List[str] and value is a List[Any]: filters by multiple AND conditions
        where col[i] must equal value[i]. The lists must be the same length
        """
        if isinstance(col, str) and not isinstance(value, list):
            # --- Handle Single Condition ---
            single_col_name = col
            single_value = value
            if single_col_name not in self.data.columns:
                raise ValueError(f"Column '{single_col_name}' not found in DataFrame")
            if not (self.data[single_col_name]== single_value).any():
                print(f"Warning: Value '{single_value}' not found in column '{single_col_name}'.")
            return self.data.loc[self.data[single_col_name]==single_value]
        elif isinstance(col, list) and isinstance(value,list):
            # ---Handle Multiple AND Conditions ---
            cols_list = col
            values_list = value

            if len(cols_list) != len(values_list):
                raise ValueError("The 'col' list and 'value' list must be of the same length for paired conditions")
            
            if not cols_list:
                return self.data.copy()
            combined_condition = pd.Series([True] * len(self.data), index = self.data.index)

            for i in range(len(cols_list)):
                col_name = cols_list[i]
                val_to_filter = values_list[i]

                if col_name not in self.data.columns:
                    raise ValueError(f"Filter error: Column '{col_name}' not found in DataFrame.")
                
                combined_condition &= (self.data[col_name] == val_to_filter)
            
            return self.data.loc[combined_condition]
        
        else:
            raise TypeError("Invalid combination of types for 'col' and 'value'. "
                            "Provide (str, Any) for a single filter, or (List[str], List[Any])"
                            "for multiple AND filters. ")
        
    # def data_drop(self,col:str):
    #     self.data = self.data.drop(col,axis=1)
    #     return self.data
    def get_shaped_dataframe(
            base_df = pd.DataFrame,
            include_columns: Optional[List[str]] = None,
            exclude_columns: Optional[List[str]] = None

        ) -> pd.DataFrame:
            """
            Applies column inclusion or exclusion to a DataFrame.
            If include_columns is provided, only those columns are kept.
            Else if exclude_columns is provided, those columns are dropped.
            Returns a new DataFrame
            """
            current_df = base_df.copy()

            if include_columns:
                #Filter include_columns to only those that actually exist in current_df
                valid_include_cols = [col for col in include_columns if col in current_df.columns]
                if not valid_include_cols and include_columns:
                    print(f"Warning: None of the specified include_columns {include_columns} exist ")
    def categorical_data(self):
        cat_columns = self.data.select_dtypes(['object','bool','category','integer']).columns.tolist()
        cat_data = self.data[cat_columns]
        return cat_data

    def frequency_table(self,column_name:str, **kwargs):
        cat_data = self.data.select_dtypes(['bool','category','object']).columns.tolist()
        if not isinstance(column_name, str) or (column_name not in cat_data):
            raise ValueError(f"{column_name} is not a string or not in features")
        crosstab_params = {"columns": "count"}  # Default for a simple frequency table
        crosstab_params.update(kwargs) 
        table = pd.crosstab(index=self.data[column_name], **crosstab_params)
        return table
    def cross_tabs(self, index_names:list, columns_names:list, normalize = False, margins=False, **kwargs):
        cat_data = self.categorical_data()
        prepared_indexes = [cat_data[name] for name in index_names]
        prepared_columns = [cat_data[name] for name in columns_names]
        cross_tab_table = pd.crosstab(
            index=prepared_indexes,
            columns=prepared_columns,
            normalize=normalize,
            margins=margins
        )
        return cross_tab_table
    

class Diamonds(Descriptive):
    def __init__(self):
        diamonds_df = sns.load_dataset('diamonds')
        super().__init__(diamonds_df)
    def price_per_carat(self):
        self.data['price_per_carat'] = round(self.data['price']/self.data['carat'],2)
        return self.data



if __name__=="__main__":
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.width', 1000) # Adjust for your console width
    diamonds = Diamonds()
    print(diamonds.check_unique_counts())
    print(diamonds.check_rows_and_columns_counts())
    print(diamonds.categorical_describe())
    print(diamonds.numerical_describe())
    print(diamonds.data_info())
    print(diamonds.data_filter('cut','Ideal'))
    df = diamonds.price_per_carat()
    df["high_price"] = np.where(df['price_per_carat']>3500,1,0)
    print(df)
    def multiply(x):
        y = 1.3 * x
        return y
    df['price_per_carat_with taxes']= df['price_per_carat'].apply(multiply)
    #df = diamonds.data_drop(['carat', 'cut', 'color'])
    print(df.head())
    df.to_csv("diamonds.csv",index = False)
    print(diamonds.frequency_table(column_name='cut'))
    cross_tab_result = diamonds.cross_tabs(index_names=['cut'],columns_names=['clarity','color'])
    stacked_by_color = cross_tab_result.stack(level='color',future_stack=True)
    print(stacked_by_color)

    print(diamonds.data_filter(col=['cut'], value=['Ideal']))
    

