# api_data_manager.py
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path
import seaborn as sns
import traceback
import csv

# --- Dataset Discovery and Management ---

# This assumes 'api_data_manager.py' is in your 'full_stack_project' root,
# and 'datasets' is a subfolder also in 'full_stack_project'.
PROJECT_ROOT_DIR = Path(__file__).resolve().parent 
DATASETS_DIR = PROJECT_ROOT_DIR / "datasets"

# In api_data_manager.py

def discover_datasets() -> Dict[str, Path]:
    """
    Scans the DATASETS_DIR for .csv files, including known subfolders.
    Returns a dictionary mapping a unique dataset key (display name) to its file Path object.
    """
    available_files: Dict[str, Path] = {}
    if not DATASETS_DIR.is_dir():
        print(f"ERROR: Datasets directory '{DATASETS_DIR}' not found.")
        return available_files

    # 1. Scan for CSVs directly in the root datasets/ folder
    for f_path in DATASETS_DIR.glob("*.csv"):
        # Key is based on filename, e.g., 'penguins.csv' -> 'penguins'
        dataset_name_key = f_path.stem.lower().replace('-', '_').replace(' ', '_') 
        available_files[dataset_name_key] = f_path
        print(f"Discovered root CSV: '{dataset_name_key}' at {f_path}")

    # 2. Scan for CSVs in specified subfolders
    subfolders_to_scan = ["student", "bank-additional"]
    for subfolder in subfolders_to_scan:
        data_sub_dir = DATASETS_DIR / subfolder
        if data_sub_dir.is_dir():
            for f_path in data_sub_dir.glob("*.csv"):
                # Key is based on filename, e.g., 'student-mat.csv' -> 'student_mat'
                dataset_name_key = f_path.stem.lower().replace('-', '_').replace(' ', '_')
                
                # In case of a name collision (e.g., 'data.csv' in root and in subfolder),
                # prepend the folder name to the key to make it unique.
                if dataset_name_key in available_files:
                    dataset_name_key = f"{subfolder.replace('-', '_')}_{dataset_name_key}"

                available_files[dataset_name_key] = f_path
                print(f"Discovered subfolder CSV: '{dataset_name_key}' at {f_path}")
    
    return available_files

AVAILABLE_DATASETS: Dict[str, Path] = discover_datasets()
print(f"INFO: Available datasets initialized: {list(AVAILABLE_DATASETS.keys())}")

_active_data_manager: Optional['BaseDataManager'] = None 
_active_dataset_name: Optional[str] = None

def get_active_data_manager() -> 'BaseDataManager':
    """Returns the currently active data manager. Loads a default if none is active."""
    global _active_data_manager
    if _active_data_manager is None:
        print("INFO: No active data manager. Attempting to load a default dataset.")
        default_key = "diamonds" if "diamonds" in AVAILABLE_DATASETS else (list(AVAILABLE_DATASETS.keys())[0] if AVAILABLE_DATASETS else None)
        if default_key and load_dataset(default_key):
            return _active_data_manager
        else:
            raise RuntimeError("Could not load a default dataset. No datasets found or default failed to load.")
    return _active_data_manager

def load_dataset(dataset_key: str) -> bool:
    """Loads the specified dataset by its key, makes it active, and prepares it."""
    global _active_data_manager, _active_dataset_name
    if dataset_key not in AVAILABLE_DATASETS:
        print(f"ERROR: Dataset key '{dataset_key}' not found.")
        return False
    
    file_path = AVAILABLE_DATASETS[dataset_key]
    print(f"INFO: Attempting to load dataset '{dataset_key}' from path: {file_path}")
    try:
        new_manager = CSVDataManager(file_path=str(file_path), source_name=dataset_key)
        new_manager.load_and_prepare_data()
        _active_data_manager = new_manager
        _active_dataset_name = dataset_key
        print(f"INFO: Dataset '{dataset_key}' loaded and set as active.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to load and prepare dataset '{dataset_key}': {e}")
        traceback.print_exc()
        return False

# --- Data Manager Classes ---

class BaseDataManager(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name
        self._processed_df: Optional[pd.DataFrame] = None
        self._is_loaded: bool = False

    @abstractmethod
    def _load_data_from_source(self) -> pd.DataFrame:
        pass

    def load_and_prepare_data(self) -> None:
        if self._is_loaded:
            return
        print(f"DataManager: Loading and preparing data for '{self.source_name}'...")
        try:
            df = self._load_data_from_source()
            self._processed_df = self._post_process_data(df)
            self._is_loaded = True
            print(f"DataManager: Data for '{self.source_name}' loaded and prepared.")
        except Exception as e:
            print(f"ERROR: DataManager failed to load data for '{self.source_name}': {e}")
            raise

    def _post_process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()
        print(f"INFO: Running _post_process_data for {self.source_name}")

        if self.source_name == "diamonds":
            if 'price' in df_copy.columns and 'carat' in df_copy.columns:
                non_zero_carat = df_copy['carat'] != 0
                df_copy.loc[non_zero_carat, 'price_per_carat'] = round(df_copy.loc[non_zero_carat, 'price'] / df_copy.loc[non_zero_carat, 'carat'], 2)
                if 'price_per_carat' in df_copy.columns:
                    df_copy["high_price"] = np.where(df_copy['price_per_carat'] > 3500, 1, 0)
        
        if "student" in self.source_name:
            if all(col in df_copy.columns for col in ['G1', 'G2', 'G3']):
                df_copy['average_grade'] = round((df_copy['G1'] + df_copy['G2'] + df_copy['G3']) / 3, 2)
                print("INFO: Calculated 'average_grade' for student dataset.")
                
        return df_copy
    
    def get_processed_df(self) -> pd.DataFrame:
        if not self._is_loaded or self._processed_df is None:
            raise RuntimeError(f"Data for '{self.source_name}' not loaded. Call load_dataset() first.")
        return self._processed_df.copy()
    
    def get_column_names(self) -> List[str]:
        return self.get_processed_df().columns.tolist()
    
    def get_categorical_column_names(self) -> List[str]:
        df = self.get_processed_df()
        categorical_cols_list = df.select_dtypes(include=['category', 'object']).columns.tolist()
        int_columns = df.select_dtypes(include='integer').columns
        for col_name in int_columns:
            if col_name not in categorical_cols_list:
                if df[col_name].nunique() < 20:
                    categorical_cols_list.append(col_name)
        return list(dict.fromkeys(categorical_cols_list))
    
    def get_numerical_data_column_names(self) -> List[str]:
        return self.get_processed_df().select_dtypes(include=np.number).columns.tolist()

class CSVDataManager(BaseDataManager):
    def __init__(self, file_path: str, source_name: Optional[str] = None):
        super().__init__(source_name=source_name or Path(file_path).stem)
        self.file_path = file_path

# In api_data_manager.py, inside the CSVDataManager class

    ### START: REPLACE THIS ENTIRE METHOD ###
    def _load_data_from_source(self) -> pd.DataFrame:
        print(f"CSVDataManager: Loading data from '{self.file_path}'...")

        delimiter = ','  # Start with comma as the default

        try:
            with open(self.file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Read a small sample of the file
                sample = csvfile.read(4096)  # Read the first 4KB
                # Use the Sniffer to deduce the delimiter from the sample
                dialect = csv.Sniffer().sniff(sample, delimiters=',;')
                delimiter = dialect.delimiter
                print(f"INFO: Auto-detected delimiter '{delimiter}' for '{self.file_path}'.")
        except (csv.Error, UnicodeDecodeError) as e:
            print(f"WARNING: Could not auto-detect delimiter, defaulting to ','. Error: {e}")
            delimiter = ',' # Fallback to comma if sniffing fails
        except Exception as e:
            print(f"WARNING: An unexpected error occurred during delimiter detection, defaulting to ','. Error: {e}")
            delimiter = ','

        # Now, read the entire CSV file using the detected (or default) delimiter
        return pd.read_csv(self.file_path, sep=delimiter)
    ### END: REPLACE THIS ENTIRE METHOD ###

if __name__ == "__main__":
    print("\n--- Testing DataManager with Multiple Datasets ---")
    print(f"Discovered datasets: {list(AVAILABLE_DATASETS.keys())}")
    if AVAILABLE_DATASETS:
        for key in AVAILABLE_DATASETS.keys():
            print(f"\n--- Loading and testing dataset: '{key}' ---")
            if load_dataset(key):
                active_manager = get_active_data_manager()
                df = active_manager.get_processed_df()
                print(f"Successfully loaded '{key}'. Shape: {df.shape}. Head:")
                print(df.head())
                print(f"Categorical columns: {active_manager.get_categorical_column_names()}")
            else:
                print(f"--- FAILED to load dataset: {key} ---")