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
    # def cross_tabs(self, index_names:list, columns_names:list, normalize = False, margins=False, **kwargs):
    #     cat_data = self.categorical_data()
    #     prepared_indexes = [cat_data[name] for name in index_names]
    #     prepared_columns = [cat_data[name] for name in columns_names]
    #     cross_tab_table = pd.crosstab(
    #         index=prepared_indexes,
    #         columns=prepared_columns,
    #         normalize=normalize,
    #         margins=margins
    #     )
    #     return cross_tab_table
    # In original_descriptive.py, inside the Descriptive class
    def cross_tabs(self, index_names:list, columns_names:list, normalize = False, margins=False, **kwargs):
        cat_data = self.categorical_data()

        print(f"\n--- DEBUG: Inside Descriptive.cross_tabs ---")
        print(f"Received index_names: {index_names}")
        print(f"Received columns_names: {columns_names}")
        print(f"Received normalize: {normalize}, margins: {margins}, kwargs: {kwargs}")
        print(f"Shape of self.data (passed to this instance): {self.data.shape}")

        # Validate names are in cat_data before list comprehension
        for name in index_names:
            if name not in cat_data: 
                err_msg = f"Index name '{name}' not found in categorical data for crosstab. Available in cat_data: {cat_data.columns.tolist()}"
                print(f"ERROR: {err_msg}")
                raise ValueError(err_msg)
        for name in columns_names:
            if name not in cat_data: 
                err_msg = f"Column name '{name}' not found in categorical data for crosstab. Available in cat_data: {cat_data.columns.tolist()}"
                print(f"ERROR: {err_msg}")
                raise ValueError(err_msg)

        prepared_indexes = [cat_data[name] for name in index_names]
        prepared_columns = [cat_data[name] for name in columns_names]

        try:
            print("Attempting pd.crosstab...")
            cross_tab_table = pd.crosstab(
                index=prepared_indexes,
                columns=prepared_columns,
                normalize=normalize,
                margins=margins,
                **kwargs 
            )
            print("DEBUG Descr.cross_tabs: pd.crosstab successful, shape:", cross_tab_table.shape)
            return cross_tab_table
        except Exception as e:
            print(f"!!!!!!!! ERROR INSIDE Descriptive.cross_tabs during pd.crosstab !!!!!!!!") # Make it stand out
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {e}")
            import traceback
            print("Full Traceback from Descriptive.cross_tabs:")
            traceback.print_exc() # This will print the full Python traceback
            print(f"--------------------------------------------------------------------")
            raise # Re-raise the error
    

class Diamonds(Descriptive):
    def __init__(self):
        diamonds_df = sns.load_dataset('diamonds')
        super().__init__(diamonds_df)
    def price_per_carat(self):
        self.data['price_per_carat'] = round(self.data['price']/self.data['carat'],2)
        return self.data



# In original_descriptive.py

# ... (your Descriptive and Diamonds class definitions above) ...

if __name__=="__main__":
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.width', 1000)
    
    print("--- Initializing Diamonds instance ---")
    diamonds_instance = Diamonds() # Use a consistent name, e.g., diamonds_instance

    print("\n--- Testing basic descriptive methods ---")
    print(diamonds_instance.check_unique_counts())
    print(diamonds_instance.check_rows_and_columns_counts())
    print("\nCategorical Describe:")
    print(diamonds_instance.categorical_describe())
    print("\nNumerical Describe:")
    print(diamonds_instance.numerical_describe())
    print("\nData Info:")
    # data_info() prints to stdout and returns None, so calling it directly is fine for testing.
    # If you want to capture its string output here like the handler does:
    # import io
    # buffer = io.StringIO()
    # diamonds_instance.data.info(buf=buffer)
    # print(buffer.getvalue())
    diamonds_instance.data_info() 

    print("\n--- Testing single condition data_filter ---")
    print(diamonds_instance.data_filter('cut','Ideal').head()) # Show head to keep output manageable

    print("\n--- Performing feature engineering and saving CSV ---")
    # Note: price_per_carat modifies diamonds_instance.data in-place
    df_engineered = diamonds_instance.price_per_carat() 
    # It's better practice if methods that transform data return a new df
    # or clearly document in-place modification. For now, this is fine.
    df_engineered["high_price"] = np.where(df_engineered['price_per_carat'] > 3500, 1, 0)
    
    def multiply(x):
        y = 1.3 * x
        return y
    df_engineered['price_per_carat_with taxes'] = df_engineered['price_per_carat'].apply(multiply)
    print("\nEngineered DataFrame head:")
    print(df_engineered.head())
    # The df_engineered is the same object as diamonds_instance.data now.
    # df_engineered.to_csv("diamonds.csv", index=False) # Ensure this uses the most up-to-date df
    diamonds_instance.data.to_csv("diamonds.csv", index=False) # Save the instance's data
    print("diamonds.csv saved.")

    print("\n--- Testing frequency_table ---")
    print(diamonds_instance.frequency_table(column_name='cut'))

    print("\n--- Testing cross_tabs(index=['cut'], columns=['clarity', 'color']) and stack ---")
    try:
        cross_tab_result_1 = diamonds_instance.cross_tabs(index_names=['cut'], columns_names=['clarity', 'color'])
        print("cross_tab_result_1 created. Shape:", cross_tab_result_1.shape)
        
        print("\ncross_tab_result_1.columns:")
        print(cross_tab_result_1.columns)
        print("cross_tab_result_1.columns.names (Key for stack level names):")
        print(cross_tab_result_1.columns.names) 
        print("------------------------------------------------------------\n")

        print("Attempting to stack cross_tab_result_1 by level 'color'...")
        stacked_by_color = cross_tab_result_1.stack(level='color', future_stack=True)
        print("Stacked by 'color' successfully. Head of stacked data:")
        print(stacked_by_color.head())

    except KeyError as e:
        print(f"CAUGHT KEY ERROR during stack: {e}")
        print("This likely means 'color' (or the specified level) was not a recognized level name in cross_tab_result_1.columns.names.")
        print("Check the printed 'cross_tab_result_1.columns.names' above.")
    except Exception as e:
        print(f"An unexpected error occurred with crosstab_1 or stack: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
    print("---------------------------------------------------------------------\n")

    print("\n--- Testing polymorphic data_filter with list inputs ---")
    # This uses the diamonds_instance which has had columns added to its .data attribute
    print(diamonds_instance.data_filter(col=['cut', 'high_price'], value=['Ideal', 1]).head())


    print("\n--- Testing 2-index vs 2-column Cross-Tabulation Directly (that caused API error) ---")
    test_index_names_2x2 = ['high_price', 'color']
    test_columns_names_2x2 = ['clarity', 'cut']
    
    # Test first with margins=False (default)
    print(f"\nAttempting 2x2 crosstab with index: {test_index_names_2x2}, columns: {test_columns_names_2x2}, margins: False")
    try:
        crosstab_result_2x2_no_margins = diamonds_instance.cross_tabs(
            index_names=test_index_names_2x2,
            columns_names=test_columns_names_2x2,
            margins=False 
        )
        print("2x2 Crosstab (margins=False) successful. Shape:", crosstab_result_2x2_no_margins.shape)
        # print("Head of 2x2 Crosstab (margins=False):")
        # print(crosstab_result_2x2_no_margins.head()) # Optional: print part of the result
    except Exception as e:
        print(f"ERROR generating 2x2 crosstab (margins=False): {type(e).__name__} - {e}")
        import traceback
        print("Full traceback for 2x2 margins=False error:")
        traceback.print_exc()

    print("\n---")
    
    # Test with margins=True
    print(f"Attempting 2x2 crosstab with index: {test_index_names_2x2}, columns: {test_columns_names_2x2}, margins: True")
    try:
        crosstab_result_2x2_with_margins = diamonds_instance.cross_tabs(
            index_names=test_index_names_2x2,
            columns_names=test_columns_names_2x2,
            margins=True 
        )
        print("2x2 Crosstab (margins=True) successful. Shape:", crosstab_result_2x2_with_margins.shape)
        # print("Head of 2x2 Crosstab (margins=True):")
        # print(crosstab_result_2x2_with_margins.head()) # Optional: print part of the result
    except Exception as e:
        print(f"ERROR generating 2x2 crosstab (margins=True): {type(e).__name__} - {e}")
        import traceback
        print("Full traceback for 2x2 margins=True error:")
        traceback.print_exc()
    
    print("\n--- End of All Tests ---")