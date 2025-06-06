import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from pathlib import Path
import seaborn as sns

PROJECT_ROOT_DIR = Path(__file__).resolve().parent
DATASETS_DIR = PROJECT_ROOT_DIR / "datasets"

def discover_datasets() -> Dict[str, Path]:
    """
    Scans the DATASETS_DIR for .csv files.
    Looks for CSVs directly in DATASETS_DIR and in known subfolders.
    Returns a dictionary mapping a unique dataset key (display name) to its file Path object
    """

    available_files: Dict[str, Path] = {}
    if not DATASETS_DIR.is_dir():
        print(f"ERROR: Datasets directory '{DATASETS_DIR}' not found. Please creat it or update the path. ")
        return available_files
    #1 Direct CSVs in datasets/ (e.g. diamonds.csv, and penguins.csv)
    for f_path in DATASETS_DIR.glob("*.csv"):
        dataset_name_key = f_path.stem.lower().replace('-', '_').replace(' ', '_')
        available_files[dataset_name_key] = f_path
        print(f"Discovered direct CSV: '{dataset_name_key}' at {f_path}")

    #2 CSVs in student subfolder
    student_dir = DATASETS_DIR / "student"
    if student_dir.is_dir():
        for f_path in student_dir.glob("*.csv"):
            dataset_name_key = f"student_{f_path.stem.lower().replace('-', '_').replace(' ', '_')}"
            available_files[dataset_name_key] = f_path
            print(f"Discovered direct CSV: '{dataset_name_key}' at {f_path}")
    else:
        print(f"INFO: Subdirectory 'student' not found in '{DATASETS_DIR}'." )


    bank_dir = DATASETS_DIR / "bank-additional"
    if bank_dir.is_dir():
        for f_path in bank_dir.glob("*.csv"): 
            dataset_name_key = f"bank_{f_path.stem.lower().replace('-', '_').replace(' ', '_')}" 
            available_files[dataset_name_key] = f_path
            print(f"Discovered bank CSV: '{dataset_name_key}' at {f_path}")
    else:
        print(f"INFO: Subdirectory 'bank-additional' not found in '{DATASETS_DIR}'.")
    
    if not available_files:
        print(f"WARNING: No CSV datasets found in '{DATASETS_DIR}' or specified subfolders.")
        
    return available_files

AVAILABLE_DATASETS: Dict[str, Path] = discover_datasets()
print(f"INFO: Available datasets initialized: {AVAILABLE_DATASETS}")

_active_data_manager: Optional['BaseDataManager'] = None 
_active_dataset_name: Optional[str] = None

def get_active_data_manager() -> 'BaseDataManager':
    global _active_data_manager
    global _active_dataset_name
    if _active_data_manager is None:
        print("INFO: No active data manager. Attempting to load a default dataset.")
        default_key_to_load = None
        if "diamonds" in AVAILABLE_DATASETS: # Prioritize 'diamonds' if available
            default_key_to_load = "diamonds"
        elif AVAILABLE_DATASETS: 
            default_key_to_load = list(AVAILABLE_DATASETS.keys())[0]
        
        if default_key_to_load:
            if not load_dataset(default_key_to_load): # Check if loading failed
                 # If default load failed, create empty manager as a last resort
                print(f"ERROR: Default dataset '{default_key_to_load}' failed to load. Creating an empty manager.")
                _active_data_manager = CSVDataManager(file_path=None, df_override=pd.DataFrame(), source_name="empty_fallback")
                _active_data_manager._is_loaded = True 
                _active_data_manager._processed_df = pd.DataFrame()
                _active_dataset_name = "empty_fallback"
        else:
            print("ERROR: No datasets found to load as default. Creating an empty manager.")
            _active_data_manager = CSVDataManager(file_path=None, df_override=pd.DataFrame(), source_name="empty_no_datasets")
            _active_data_manager._is_loaded = True
            _active_data_manager._processed_df = pd.DataFrame()
            _active_dataset_name = "empty_no_datasets"

    if _active_data_manager is None: 
        raise RuntimeError("Critical error: Active data manager could not be initialized after default load attempt.")
        
    return _active_data_manager

def load_dataset(dataset_key: str) -> bool:
    global _active_data_manager
    global _active_dataset_name
    
    if dataset_key not in AVAILABLE_DATASETS:
        print(f"ERROR: Dataset key '{dataset_key}' not found in AVAILABLE_DATASETS: {AVAILABLE_DATASETS.keys()}")
        return False
    
    file_path = AVAILABLE_DATASETS[dataset_key]
    print(f"INFO: Attempting to load dataset '{dataset_key}' from path: {file_path}")
    
    try:
        # Use str(file_path) for CSVDataManager
        new_manager = CSVDataManager(file_path=str(file_path), source_name=dataset_key)
        new_manager.load_and_prepare_data() 
        
        _active_data_manager = new_manager
        _active_dataset_name = dataset_key
        print(f"INFO: Dataset '{dataset_key}' loaded and set as active.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to load and prepare dataset '{dataset_key}': {e}")
        # import traceback # Already imported at the top of the file usually
        # traceback.print_exc() # For more detail on the error during loading
        _active_data_manager = None 
        _active_dataset_name = None
        return False
### END: ADD THIS NEW CODE ###


            


class BaseDataManager(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name
        self._processed_df: Optional[pd.DataFrame] = None
        self._is_loaded: bool = False

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
        df = self.get_processed_df()
        cat_names = df.select_dtypes(include=['object','category']).columns.tolist()
        int_names = df.select_dtypes(include=['integer', 'int8', 'int16', 'int64']).columns
        for column_name in int_names:
            if column_name not in cat_names:
                if df[column_name].nunique() < 15:
                    cat_names.append(column_name)
        return list(dict.fromkeys(cat_names))
    
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
    def __init__(self, file_path: Optional[str], source_name: Optional[str] = None, df_override: Optional[pd.DataFrame] = None):
        self._df_override = df_override
        self.file_path = file_path

        _source_name_to_use = source_name
        if not _source_name_to_use and file_path:
            _source_name_to_use = Path(file_path).stem.lower().replace('-', '_').replace(' ', '_')
        elif not _source_name_to_use and df_override is not None:
            _source_name_to_use = "loaded_dataframe_manager"

        super().__init__(source_name=_source_name_to_use if _source_name_to_use else "unknown_csv_source")

        if self._df_override is not None:
            self._processed_df = self._df_override
            self._is_loaded = True
            print(f"CSVDataManager initialized with an overrideen DataFrame for source: '{self.source_name}'.")

    
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

# ### REPLACE YOUR if __name__ == "__main__": BLOCK WITH THIS for testing ###
if __name__ == "__main__":
    print("\n--- Testing DataManager with Multiple Datasets ---")
    print(f"Discovered datasets by discover_datasets(): {AVAILABLE_DATASETS}")

    if AVAILABLE_DATASETS:
        # Test loading each discovered dataset
        for key in AVAILABLE_DATASETS.keys():
            print(f"\n--- Attempting to load and test dataset: '{key}' ---")
            success = load_dataset(key) # This function now also calls load_and_prepare_data
            if success:
                active_manager = get_active_data_manager() # Should return the manager for 'key'
                if active_manager.source_name == key:
                    try:
                        df = active_manager.get_processed_df()
                        print(f"Successfully loaded and processed '{key}'. DataFrame head:")
                        print(df.head())
                        print(f"Numerical columns for '{key}': {active_manager.get_numerical_data_column_names()}")
                        print(f"Categorical columns for '{key}': {active_manager.get_categorical_column_names()}")
                    except Exception as e:
                        print(f"Error getting processed df for '{key}': {e}")
                else:
                    print(f"ERROR: Active manager source name '{active_manager.source_name}' does not match expected '{key}'")
            else:
                print(f"Failed to load dataset: {key}")
        
        # Test default loading by resetting active manager
        print("\n--- Testing get_active_data_manager for default loading ---")
        _active_data_manager = None 
        _active_dataset_name = None
        try:
            default_loaded_manager = get_active_data_manager()
            if default_loaded_manager and default_loaded_manager._is_loaded:
                df_default = default_loaded_manager.get_processed_df()
                print(f"Default loaded dataset '{default_loaded_manager.source_name}' head:")
                print(df_default.head())
            else:
                print("Default loading did not result in a loaded manager.")
        except Exception as e:
            print(f"Error during default loading test: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No datasets discovered to test.")
