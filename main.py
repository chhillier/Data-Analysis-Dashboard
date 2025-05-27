from api_data_manager import default_data_manager
import pandas as pd
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query, Body
import api_descriptive_handlers as desc_api
import api_plot_handlers as plots_api
import schemas

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    print("FastAPI application startup (using lifespan)...")
    try:
        default_data_manager.load_and_prepare_data()
        print("Data loading process via DataManager initiated successfully during lifespan startup")
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR during lifespan: DataManager failed to load data {e}")
    yield
    print("FastAPI application shutting down (lifespan)...")

app = FastAPI(
    lifespan=lifespan,
    title="Descriptive Statistics and Plotting API (Class-based DM with Lifespan)",
    description="API to serve data summaries and plots",
    version="0.1.0"
)

def get_dataframe_dependency() -> pd.DataFrame:
    """Dependency funtion to get the processed DataFrame from the DataManager instance"""
    try:
        return default_data_manager.get_processed_df()
    except RuntimeError as e:
        print(f"Error in get_dataframe_dependency: {e}")
        raise HTTPException(status_code=503, detail= f"Service temporarily unavailable: Data not loaded - {str(e)}")

"""API Endpoints"""
TAG_DATA_INFO = "Data Information"
TAG_DESCRIPTIVE = 'Descriptive Statistics'
TAG_STATIC_PLOTS = "Static Plots"
TAG_STATISTIC_OUTPUT = "Classical Statistic Analysis"
TAG_STATISTICAL_PLOTS = "Statistical Plots"
TAG_INTERACTIVE_PLOTS = "Interactive Plots"


@app.get("/api/health", tags=["General"])
async def health_check():
    is_data_loaded = False
    if hasattr(default_data_manager, '_is_loaded'):
        is_data_loaded = default_data_manager._is_loaded
    return {"status": "API is running", "data_manager_initialized": True, "data_loaded_successfully": is_data_loaded}

@app.get("/api/descriptive/frequency-table", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameSplitResponse])

async def get_frequency_table_endpoint(
    column_name: str = Query(..., description="The categorical column name to generate a frequency table for.", examples=["cut"]),
    df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """
    Get a frequency table (counts) for a given categorical column.
    Make sure the api_descriptive_handler.py has:
    def handle_frequency_table(des_instance: Descriptive, column_name: str, **kwargs)
        ... (logic using des_instance.frequency_table) ...
        return freq_table_df.to_dict("split")
    """
    #try:



