from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

"""
Explanation of Code:

This file (`schemas.py`) is basically about defining the 'shape' of the data 
our API expects to receive and the 'shape' of the data it will send back. 
We use something called Pydantic models here – you can think of them as clear 
templates or 'blueprints' for our data. Our FastAPI web framework uses these 
Pydantic blueprints to automatically:
1.  Check incoming data: It makes sure any data sent to our API is correct 
    (e.g., has the right data types like numbers or text, and includes all 
    the necessary pieces of information).
2.  Handle data conversion: It smoothly changes our data between Python's way 
    of thinking and JSON (which is how data is usually sent over the web).
3.  Create API documentation: It builds helpful 'how-to-use' guides for our API 
    automatically, so it's clear what data to send and what you'll get back.

Sometimes, just knowing a piece of data is a number or text isn't enough. 
That's where `Field` (which we get from Pydantic) helps out. `Field` lets us 
add extra details to our data blueprints. For example, we can use it to write a 
description of what a data field means, show some examples of what it should look 
like, or even set specific rules (like 'this number must be between 1 and 100'). 
This makes our API more reliable and use correctly.
"""

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
    bins: Optional[int] = None
    kde: Optional[bool] = None
    stat: Optional[str] = None
    # edgecolor: Optional[str] = None
    kde_line_color: Optional[str] = None

    # For KDE

    fill: Optional[bool] = None
    alpha: Optional[float] = None
    linewidth: Optional[float] = None


    # For scatter
    col_name_x: Optional[str] = None
    col_name_y: Optional[str] = None
    s: Optional[int] = None

    # For bar_chart
    x_col: Optional[str] = None
    y_col: Optional[str] = None
    estimator: Optional[str] = None
    errorbar: Optional[Union[str, tuple, None]] = ('ci', 95) # Matches sns.barplot default
    palette: Optional[str] = None

    # For crosstab_heatmap
    index_names_ct: Optional[List[str]] = None
    column_names_ct: Optional[List[str]] = None
    annot: Optional[bool] = True
    fmt: Optional[str] = 'd'
    cmap: Optional[str] = 'viridis'
    annot_kws: Optional[Dict[str, Any]] = None

    kind: Optional[str] = None

    #For count plot
    dodge: Optional[bool] = None

    #Put more graphs here

    class Config:
        pass

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

class CrossTabRequest(BaseModel):
    index_names: List[str] = Field(..., examples=[["cut"], ["cut", "clarity"]])
    column_names: List[str] = Field(..., examples=[["color"], ["color", "cut"]])
    normalize: bool = False
    margins: bool = False

class FilterConditionRequest(BaseModel):
    cols: List[str] = Field(..., examples = [["cut"], ["cut", "color"]])
    values: List[Any] = Field(..., examples=[["Ideal"], ["Ideal", "E"]])




