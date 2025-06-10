# main.py
import pandas as pd 
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query, Body 
from fastapi.responses import StreamingResponse

# Import your custom modules
from api_data_manager import get_active_data_manager, load_dataset, AVAILABLE_DATASETS
import api_descriptive_handlers as desc_api
import api_plot_handlers as plots_api
import schemas

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup logic. Calls get_active_data_manager() 
    to ensure a default dataset is loaded when the API starts.
    """
    print("FastAPI application startup (using lifespan)...")
    try:
        get_active_data_manager()
        print("Default data loading process initiated successfully during lifespan startup.")
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR: Could not initialize default data manager: {e}")
    yield
    print("FastAPI application shutting down (lifespan)...")

# --- FastAPI Application Instance ---
app = FastAPI(
    lifespan=lifespan, 
    title="Data Analysis and Plotting API",
    description="API to serve data summaries and plots from the loaded dataset.",
    version="1.0.0"
)

# --- Dependency to get DataFrame ---
def get_dataframe_dependency() -> pd.DataFrame:
    """
    Dependency function to get the processed DataFrame from the CURRENTLY ACTIVE
    data manager instance.
    """
    try:
        active_manager = get_active_data_manager()
        return active_manager.get_processed_df()
    except RuntimeError as e:
        print(f"Error in get_dataframe_dependency: {e}")
        raise HTTPException(status_code=503, detail=f"Service Temporarily Unavailable: {e}")

# --- API Tags ---
TAG_GENERAL = "General & Dataset Management"
TAG_DATA_INFO = "Data Information"
TAG_DESCRIPTIVE = 'Descriptive Statistics'
TAG_PLOTS = "Plot Generation"

# --- General & Dataset Endpoints ---
@app.get("/api/health", tags=[TAG_GENERAL])
async def health_check():
    """Check if the API is running and a dataset is loaded."""
    try:
        active_manager = get_active_data_manager()
        return {
            "status": "API is running", 
            "data_loaded": active_manager._is_loaded,
            "active_dataset": active_manager.source_name
        }
    except Exception as e:
        return {"status": "API is running but in a degraded state", "data_loaded": False, "error": str(e)}

@app.get("/api/datasets", response_model=schemas.DatasetListResponse, tags=[TAG_GENERAL])
async def list_available_datasets():
    """Lists the names of all discovered datasets that can be loaded."""
    return {"datasets": list(AVAILABLE_DATASETS.keys())}

@app.post("/api/datasets/select/{dataset_key}", response_model=schemas.StatusResponse, tags=[TAG_GENERAL])
async def select_active_dataset(dataset_key: str):
    """Loads a dataset, making it active for all other endpoints."""
    print(f"API: Received request to load dataset: '{dataset_key}'")
    success = load_dataset(dataset_key)
    if success:
        active_manager = get_active_data_manager()
        return {"status": "success", "message": f"Successfully loaded and activated dataset: '{active_manager.source_name}'"}
    else:
        raise HTTPException(status_code=404, detail=f"Dataset with key '{dataset_key}' not found or failed to load.")

@app.get("/api/data/columns", tags=[TAG_DATA_INFO])
async def get_columns_info_endpoint():
    """Get all, categorical, and numerical column names from the active dataset."""
    try:
        active_manager = get_active_data_manager()
        return {
            "all_columns": active_manager.get_column_names(),
            "categorical_columns": active_manager.get_categorical_column_names(),
            "numerical_columns": active_manager.get_numerical_data_column_names()
        }
    except RuntimeError as e: 
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {str(e)}")

# --- Descriptive Statistics Endpoints ---
@app.get("/api/descriptive/shape", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.ShapeResponse])
async def get_shape_endpoint(df: pd.DataFrame = Depends(get_dataframe_dependency)):
    shape_data = desc_api.handle_get_shape(df)
    return schemas.ShapeResponse(**shape_data)

@app.get("/api/descriptive/unique-counts", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.UniqueCountsResponse])
async def get_unique_counts_endpoint(df: pd.DataFrame = Depends(get_dataframe_dependency)):
    counts_dict = desc_api.handle_get_unique_counts(df)
    if counts_dict is not None:
        return schemas.UniqueCountsResponse(counts=counts_dict)
    return None

@app.get("/api/descriptive/info", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.InfoResponse])
async def get_data_info_endpoint(df: pd.DataFrame = Depends(get_dataframe_dependency)):
    info_str = desc_api.handle_data_info_string(df)
    if info_str is not None:
        return schemas.InfoResponse(info_string=info_str)
    return None

@app.get("/api/descriptive/numerical-summary", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameSplitResponse])
async def get_numerical_summary_endpoint(precision: int = Query(2, ge=0, le=10), df: pd.DataFrame = Depends(get_dataframe_dependency)):
    try:
        summary_dict = desc_api.handle_numerical_summary(base_df=df, precision=precision)
        return schemas.DataFrameSplitResponse(**summary_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/descriptive/categorical-summary", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameSplitResponse])
async def get_categorical_summary_endpoint(df: pd.DataFrame = Depends(get_dataframe_dependency)):
    try:
        summary_dict = desc_api.handle_categorical_summary(base_df=df)
        return schemas.DataFrameSplitResponse(**summary_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# In main.py

### START: REPLACE THIS ENTIRE FUNCTION ###
@app.get("/api/descriptive/frequency-table", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameSplitResponse])
async def get_frequency_table_endpoint(
    column_name: str = Query(..., description="The categorical column name for the frequency table."),
    # ADD these two lines to accept the parameters from the request URL
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Get a frequency table for a given categorical column, optionally after shaping."""
    try:
        table_dict = desc_api.handle_frequency_table(
            base_df=df,
            column_name=column_name,
            # Now these variables are defined and can be passed
            include_columns=include_columns,
            exclude_columns=exclude_columns
        )
        if table_dict and table_dict.get('data') is not None:
             return schemas.DataFrameSplitResponse(**table_dict)
        return schemas.DataFrameSplitResponse(index=[], columns=[], data=[]) 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in frequency-table endpoint: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
### END: REPLACE THIS ENTIRE FUNCTION ###
# In main.py

### START: REPLACE THIS ENTIRE FUNCTION ###
@app.post("/api/descriptive/cross-tabs", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameSplitResponse])
async def post_cross_tabs_endpoint(
    payload: schemas.CrossTabRequest, 
    # ADD these two lines to accept the parameters from the request URL
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Generate a cross-tabulation table, optionally after shaping."""
    try:
        table_dict = desc_api.handle_cross_tabs(
            base_df=df,
            index_names=payload.index_names, 
            columns_names=payload.column_names,
            normalize=payload.normalize,
            margins=payload.margins,
            # Now these variables are defined and can be passed
            include_columns=include_columns,
            exclude_columns=exclude_columns
        )
        if table_dict and table_dict.get('data') is not None:
            return schemas.DataFrameSplitResponse(**table_dict)
        return schemas.DataFrameSplitResponse(index=[], columns=[], data=[])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in cross-tabs endpoint: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
### END: REPLACE THIS ENTIRE FUNCTION ###@app.post("/api/descriptive/filter", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameRecordsResponse])
async def post_filter_data_endpoint(payload: schemas.FilterConditionRequest, df: pd.DataFrame = Depends(get_dataframe_dependency)):
    try:
        result_records = desc_api.handle_get_data_filter(
            base_df=df,
            filter_cols=payload.cols,
            filter_values=payload.values
        )
        return schemas.DataFrameRecordsResponse(records=result_records)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Plotting Endpoints ---
@app.post("/api/plots/dashboard", tags=[TAG_PLOTS], response_class=StreamingResponse)
async def post_dashboard_plot_endpoint(
    payload: List[schemas.PlotConfig], 
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Generate a dashboard image with one or more subplots."""
    if not payload:
        raise HTTPException(status_code=400, detail="Plot configurations list cannot be empty.")
    try:
        img_bytes_io = plots_api.handle_generate_dashboard_plot(
            base_df=base_df,
            plot_configurations=payload,
            include_columns=include_columns,
            exclude_columns=exclude_columns
        )
        if img_bytes_io is None:
            raise HTTPException(status_code=500, detail="Failed to generate plot image.")
        return StreamingResponse(img_bytes_io, media_type="image/png")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in /api/plots/dashboard endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)