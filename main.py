# main.py
import pandas as pd # Make sure pandas is imported
from typing import List, Dict, Any, Optional, Union # Union might be needed by schemas if not directly by endpoints
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query, Body # Ensure Body is imported
from fastapi.responses import StreamingResponse # For plot image responses

# Import your custom modules
from api_data_manager import default_data_manager
import api_descriptive_handlers as desc_api
import api_plot_handlers as plots_api # Ensure this is imported
import schemas # Your Pydantic models

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    print("FastAPI application startup (using lifespan)...")
    try:
        default_data_manager.load_and_prepare_data()
        print("Data loading process via DataManager initiated successfully during lifespan startup")
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR during lifespan: DataManager failed to load data: {e}")
    yield
    print("FastAPI application shutting down (lifespan)...")

# --- FastAPI Application Instance ---
app = FastAPI(
    lifespan=lifespan, 
    title="Descriptive Statistics and Plotting API",
    description="API to serve data summaries and plots from the loaded dataset.",
    version="0.1.0"
)

# --- Dependency to get DataFrame ---
def get_dataframe_dependency() -> pd.DataFrame:
    """Dependency function to get the processed DataFrame from the DataManager instance."""
    try:
        return default_data_manager.get_processed_df() # Corrected: added ()
    except RuntimeError as e:
        print(f"Error in get_dataframe_dependency: {e}")
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: Data not loaded - {str(e)}")

# --- API Tags ---
TAG_GENERAL = "General"
TAG_DATA_INFO = "Data Information"
TAG_DESCRIPTIVE = 'Descriptive Statistics'
TAG_STATIC_PLOTS = "Static Plots"
# TAG_STATISTIC_OUTPUT = "Classical Statistic Analysis" # For future
# TAG_STATISTICAL_PLOTS = "Statistical Plots" # For future
# TAG_INTERACTIVE_PLOTS = "Interactive Plots" # For future


# --- General & Data Info Endpoints ---
@app.get("/api/health", tags=[TAG_GENERAL])
async def health_check():
    """Check if the API is running and data is loaded."""
    is_data_loaded = False
    if hasattr(default_data_manager, '_is_loaded'):
        is_data_loaded = default_data_manager._is_loaded
    return {"status": "API is running", "data_manager_initialized": True, "data_loaded_successfully": is_data_loaded}

@app.get("/api/data/columns", tags=[TAG_DATA_INFO])
async def get_columns_info_endpoint():
    """Get lists of all, categorical, and numerical column names from the loaded dataset."""
    try:
        return {
            "all_columns": default_data_manager.get_column_names(),
            "categorical_columns": default_data_manager.get_categorical_column_names(),
            "numerical_columns": default_data_manager.get_numerical_data_column_names()
        }
    except RuntimeError as e: 
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {str(e)}")

# --- Descriptive Statistics Endpoints ---
@app.get("/api/descriptive/shape", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.ShapeResponse])
async def get_shape_endpoint(
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Get the number of rows and columns in the dataset, optionally after shaping."""
    # Assuming handle_get_shape in desc_api takes base_df, include_columns, exclude_columns
    shape_data = desc_api.handle_get_shape(base_df, include_columns, exclude_columns)
    return schemas.ShapeResponse(**shape_data)

@app.get("/api/descriptive/unique-counts", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.UniqueCountsResponse])
async def get_unique_counts_endpoint(
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Get unique value counts for categorical columns, optionally after shaping."""
    # Assuming handle_get_unique_counts in desc_api takes base_df, include_columns, exclude_columns
    counts_dict = desc_api.handle_get_unique_counts(base_df, include_columns, exclude_columns)
    if counts_dict is not None: # Handler might return {} if no categorical columns
        return schemas.UniqueCountsResponse(counts=counts_dict)
    return None

@app.get("/api/descriptive/info", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.InfoResponse])
async def get_data_info_endpoint(
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Get output similar to df.info() as a string, optionally after shaping."""
    # Assuming handle_data_info_string in desc_api takes base_df, include_columns, exclude_columns
    info_str = desc_api.handle_data_info_string(base_df, include_columns, exclude_columns)
    if info_str is not None:
        return schemas.InfoResponse(info_string=info_str)
    return None

@app.get("/api/descriptive/numerical-summary", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameSplitResponse])
async def get_numerical_summary_endpoint(
    precision: int = Query(2, ge=0, le=10), 
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Get numerical summary statistics, optionally after shaping."""
    try:
        summary_dict = desc_api.handle_numerical_summary(
            base_df=base_df, 
            precision=precision, 
            include_columns=include_columns, 
            exclude_columns=exclude_columns
        )
        if summary_dict and summary_dict.get('data') is not None: # Check for valid structure
            return schemas.DataFrameSplitResponse(**summary_dict)
        # Return an empty valid response if summary_dict is empty or not well-formed
        return schemas.DataFrameSplitResponse(index=[], columns=[], data=[])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in numerical-summary endpoint: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.get("/api/descriptive/categorical-summary", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameSplitResponse])
async def get_categorical_summary_endpoint(
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Get categorical summary statistics, optionally after shaping."""
    try:
        summary_dict = desc_api.handle_categorical_summary(
            base_df=base_df, 
            include_columns=include_columns, 
            exclude_columns=exclude_columns
        )
        if summary_dict and summary_dict.get('data') is not None:
            return schemas.DataFrameSplitResponse(**summary_dict)
        return schemas.DataFrameSplitResponse(index=[], columns=[], data=[])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in categorical-summary endpoint: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.get("/api/descriptive/frequency-table", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameSplitResponse])
async def get_frequency_table_endpoint(
    column_name: str = Query(..., description="The categorical column name for the frequency table.", examples=["cut"]),
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Get a frequency table for a given categorical column, optionally after shaping."""
    try:
        table_dict = desc_api.handle_frequency_table(
            base_df=base_df,
            column_name=column_name,
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

@app.post("/api/descriptive/cross-tabs", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameSplitResponse])
async def post_cross_tabs_endpoint(
    payload: schemas.CrossTabRequest, 
    include_columns: Optional[List[str]] = Query(None), # Shaping params via Query for POST
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Generate a cross-tabulation table, optionally after shaping."""
    try:
        table_dict = desc_api.handle_cross_tabs(
            base_df=base_df,
            index_names=payload.index_names, 
            columns_names=payload.column_names,
            normalize=payload.normalize,
            margins=payload.margins,
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

@app.post("/api/descriptive/filter", tags=[TAG_DESCRIPTIVE], response_model=Optional[schemas.DataFrameRecordsResponse])
async def post_filter_data_endpoint(
    payload: schemas.FilterConditionRequest, 
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Filter data based on conditions, then optionally shape columns."""
    try:
        result_records = desc_api.handle_get_data_filter(
            base_df=base_df,
            filter_cols=payload.cols,
            filter_values=payload.values,
            include_columns=include_columns,
            exclude_columns=exclude_columns
        )
        return schemas.DataFrameRecordsResponse(records=result_records) # Will be empty list if no records
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in filter endpoint: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

# --- Plotting Endpoints ---
@app.post("/api/plots/dashboard", tags=[TAG_STATIC_PLOTS], response_class=StreamingResponse)
async def post_dashboard_plot_endpoint(
    payload: List[schemas.PlotConfig], 
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Generate a dashboard image with multiple subplots."""
    if not payload:
        raise HTTPException(status_code=400, detail="plot_configurations list cannot be empty.")
    try:
        img_bytes_io = plots_api.handle_generate_dashboard_plot(
            base_df=base_df,
            plot_configurations=payload,
            include_columns=include_columns,
            exclude_columns=exclude_columns
        )
        if img_bytes_io is None:
             raise HTTPException(status_code=500, detail="Failed to generate dashboard plot image.")
        return StreamingResponse(img_bytes_io, media_type="image/png")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in /api/plots/dashboard endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating dashboard plot: {str(e)}")

@app.get("/api/plots/displot", tags=[TAG_STATIC_PLOTS], response_class=StreamingResponse)
async def get_displot_endpoint(
    col_name: str = Query(..., description="Column name for the displot."), 
    kind: str = Query(..., description="Kind of displot (e.g., 'hist', 'kde', 'ecdf')."), 
    hue_col: Optional[str] = Query(None, description="Optional column name for hue."),
    include_columns: Optional[List[str]] = Query(None),
    exclude_columns: Optional[List[str]] = Query(None),
    # Add other plot_specific_kwargs for displot as Query params if needed
    # e.g. bins: Optional[int] = Query(None)
    base_df: pd.DataFrame = Depends(get_dataframe_dependency)
):
    """Generate a distribution plot (displot)."""
    try:
        plot_specific_kwargs = {} # Collect any extra displot params here
        # if bins is not None: plot_specific_kwargs['bins'] = bins

        img_bytes_io = plots_api.handle_generate_displot(
            base_df=base_df,
            col_name=col_name,
            kind=kind,
            hue_col=hue_col,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
            **plot_specific_kwargs 
        )
        if img_bytes_io is None:
             raise HTTPException(status_code=500, detail="Failed to generate displot image.")
        return StreamingResponse(img_bytes_io, media_type="image/png")
    except ValueError as e: 
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in /api/plots/displot endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating displot: {str(e)}")
"""
--- Uvicorn runner for direct execution (optional) ---
"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)