from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- General Response Models ---

class ShapeResponse(BaseModel):
    rows : int
    columns : int

class UniqueCountsResponse(BaseModel):
    # This model expects a dictionary where keys are strings (e.g., column names or categories)
    # and values are integers (the counts)
    counts: Dict[str, int]

class InfoResponse(BaseModel):
    info_string : str

"""Plot Configuration Models (for Request Bodies)"""

class PlotParameter(BaseModel):
    #Defines the possible paramaters for individual plot functions.
    #Common params
    col_name: Optional[str] = None
    color: Optional[str] = None
    hue_col: Optional[str] = None

    # For histogram
    bins: Optional[str] = None

    # For scatter
    col_name_x: Optional[str] = None
    col_name_y: Optional[str] = None
    alpha: Optional[float] = None

    # For bar_chart
    x_col: Optional[str] = None
    y_col: Optional[str] = None
    estimator: Optional[str] = None
    errorbar: Optional[tuple[str, int] | str | None] = ('ci', 95) # Matches sns.barplot default
                                                                  # Using | for Union type hinting
    # For crosstab_heatmap
    index_names_ct: Optional[List[str]] = None
    column_names_ct: Optional[List[str]] = None
    annot: Optional[bool] = True
    fmt: Optional[str] = 'd'
    cmap: Optional[str] = 'viridis'
    annot_kws: Optional[Dict[str, Any]] = None

    #Put more graphs here

class PlotConfig(BaseModel):
    """
    Defines the configuration for a single plot within a dashboard.
    'type' specifies which plotting method to use.
    'params' holds the arguments for that plotting method.
    """
    type: str = Field(..., examples=["histogram", "kde", "scatter", "crosstab_heatmap", "bar_chart", "count_plot"],
                      description="The type of plot to generate.")
    params: PlotParameter = Field(..., description="Parameters specific to the chosen plot type.")


"""
Models for DataFrame 'split' or 'records format
If you frequently return DataFrames in these formats and want typed responses
"""

class DataFrameSplitResponse(BaseModel):
    """Structure for DataFrame.to_dict('split')"""
    index: List[Any]
    columns: List[str]
    data: List[List[Any]]

class DataFrameRecordsResponse(BaseModel):
    """Structure for DataFrame.to_dict('records') - a list of dictionaries"""
    records: List[Dict[str, Any]]


