import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List

class BaseDataManager(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name
        self._processed_df: Optional[pd.DataFrame] = None
        self._is_loaded: bool = False
        print(f"BaseDataManager initialized for source: '{self.source_name}' (Data not yet loaded). ")

    @abstractmethod
    def _load_data_from_source(self) -> pd.DataFrame:
        """Subclasses must implement this to load data from specific source"""
        pass

    def load_and_prepare_data(self) -> None:
        if self._is_loaded:
            print(f"DataManager: Data for '{self.source_name}' Data already loaded ")
            return

        print(f"DataManager: Loading and preparing data for '{self.source_name}' ... ")
        try:
            df = self._load_data_from_source()
            """Common Transformations that apply to all data"""

            """Common Transformations thata apply to all data"""
            self._processed_df = self._post_process_data(df)
            self._is_loaded = True
            print(f"DataManager: Data for '{self.source_name}' loaded and prepared")
        except Exception as e:
            self._processed_df = None
            self._is_loaded = False
            print(f"ERROR: DataManager failed to load data for '{self.source_name}': {e}")
            raise
    def _post_process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply common post-processing steps after loading"""
        """Example adding columns to the diamond dataframe"""
        if 'price' in df.columns and 'carat' in df.columns and df['carat'].ne(0).all():
            df['price_per_carat'] = round(df['price'] / df['carat'], 2)
        if 'price_per_carat' in df.columns:
            df["high_price"] = np.where(df['price_per_carat'] > 3500, 1, 0)
        return df.copy()
    
    def get_processed_df(self) -> pd.DataFrame:
        if not self._is_loaded or self._processed_df is None:
            error_msg = f"Data for '{self.source_name}' not loaded. Call load_and_prepare_data() first."
            raise RuntimeError(error_msg)
        return self._processed_df.copy()
    
    """Helper Methods START"""
    
    def get_column_names(self) -> List[str]:
        df = self.get_processed_df()
        return df.columns.tolist()
    
    def get_categorical_column_names(self) -> List[str]:
        cat_names = self.get_processed_df().select_dtypes(include=['category','object','int'])
        return cat_names.columns.tolist()
    
    def get_numerical_data_column_names(self) -> List[str]:
        num_names = self.get_processed_df().select_dtypes(include=['float', 'int'])
        return num_names.columns.tolist()
    
    """Helper Methods END"""

"""Specific DataManagers Subclasses START"""

import seaborn as sns
import numpy as np

class DiamondsDatasetManager(BaseDataManager):
    def __init__(self):
        super().__init__(source_name="diamonds_seaborn")

    def _load_data_from_source(self) -> pd.DataFrame:
        print("DiamondDatasetManager: Loading 'diamonds' dataset from Seaborn.")
        return sns.load_dataset('diamonds')
    
class CSVDataManager(BaseDataManager):
    def __init__(self, file_path: str, source_name: Optional[str] = None):
        super().__init__(source_name=source_name or file_path)
        self.file_path = file_path
    
    def _load_data_from_source(self) -> pd.DataFrame:
        print(f"CSVDataManager: Loading data from '{self.file_path}'...'")
        return pd.read_csv(self.file_path)
    
class LiveFeedDataManager(BaseDataManager):
    def __init__(self, connection_details, source_name="Live_feed_X"):
                 super().__init__(source_name)
                 self.connection_details = connection_details

    def _load_data_from_source(self) -> pd.DataFrame:
        # NEEDS logic to connect to live feed, fetch data, and convert to Dataframe
        print(f"LiveFeedDataManager: Fetching data for {self.source_name} ...")
        # more implementation
        pass
# --- Global Instance ---
# For now use the baked in dataset diamonds

default_data_manager: BaseDataManager = CSVDataManager(file_path="diamonds.csv")

# At the bottom of api_data_manager.py

# default_data_manager is already instantiated above this block as:
# default_data_manager: BaseDataManager = CSVDataManager(file_path="diamonds.csv")

if __name__ == "__main__":
    print("Testing DataManager directly...")
    try:
        # Step 1: Explicitly load and prepare the data
        print("Attempting to load and prepare data...")
        default_data_manager.load_and_prepare_data()
        print("Data load and preparation process completed by DataManager.")

        # Step 2: Now get the processed DataFrame
        print("Attempting to get processed DataFrame...")
        df = default_data_manager.get_processed_df()
        
        print("\n--- Processed DataFrame Head: ---")
        print(df.head())
        print("\n--- Processed DataFrame Info: ---")
        df.info() # .info() prints directly, doesn't return a string here unless captured
        print("\n--- Columns from DataManager: ---")
        print("All columns:", default_data_manager.get_column_names())
        print("Categorical columns:", default_data_manager.get_categorical_column_names())
        print("Numerical columns:", default_data_manager.get_numerical_data_column_names())
        
    except FileNotFoundError:
        print(f"TEST ERROR: The CSV file 'diamonds.csv' was not found. Make sure it's in the correct path.")
    except RuntimeError as e:
        print(f"TEST ERROR (RuntimeError from DataManager): {e}")
    except Exception as e:
        print(f"TEST ERROR (An unexpected error occurred): {e}")
        import traceback
        traceback.print_exc() # Print full traceback for unexpected errors


    