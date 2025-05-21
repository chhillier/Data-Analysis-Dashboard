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
    
    
        


    



    