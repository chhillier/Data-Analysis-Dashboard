# api_plot_handlers.py

import pandas as pd
import matplotlib
matplotlib.use('Agg') # Set non-interactive backend for Matplotlib - VERY IMPORTANT
import matplotlib.pyplot as plt
import io
import math
from typing import List, Dict, Any, Optional

# Assuming your StaticPlots class is in 'static_plots.py' (or 'original_static_plots.py')
# and its __init__ method accepts a DataFrame.
from static_plots import StaticPlots 
# Import the utility function for shaping data
from api_utils import get_shaped_dataframe 
# Import Pydantic models if type hinting for plot_configurations
from schemas import PlotConfig # Assuming schemas.py is accessible

# Helper to get StaticPlots instance
def get_static_plots_instance(df: pd.DataFrame) -> StaticPlots:
    """Instantiates the StaticPlots class with the given (already shaped) DataFrame."""
    return StaticPlots(df.copy()) # Pass a copy

# --- Plot Handler Functions ---

def handle_generate_dashboard_plot(
    base_df: pd.DataFrame,
    plot_configurations: List[PlotConfig], # Expecting a list of Pydantic PlotConfig models
    include_columns: Optional[List[str]] = None,
    exclude_columns: Optional[List[str]] = None
) -> Optional[io.BytesIO]:
    """
    Generates a dashboard image with multiple subplots based on configurations.
    Returns an io.BytesIO stream containing the PNG image, or None if no plots drawn.
    """
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)

    if df_to_process.empty and (include_columns or exclude_columns):
        print("Warning: DataFrame is empty after shaping for dashboard plot. No plot generated.")
        # Optionally, create a placeholder "empty" plot image
        return None 

    plots_instance = get_static_plots_instance(df_to_process)
    
    num_plots = len(plot_configurations)
    if num_plots == 0:
        print("Warning: No plot configurations provided for dashboard plot.")
        return None 

    # Determine grid size (similar to StaticPlots.subplots method)
    ncols = math.ceil(math.sqrt(num_plots))
    nrows = math.ceil(num_plots / ncols)
    
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(ncols * 5.5, nrows * 4.5), squeeze=False)
    axes_flat = axes.flatten()
    
    plot_methods_map = {
        'histogram': plots_instance.histogram,
        'kde': plots_instance.kde,
        'scatter': plots_instance.scatter,
        'crosstab_heatmap': plots_instance.crosstab_heatmap,
        'bar_chart': plots_instance.bar_chart,
        'count_plot': plots_instance.count_plot
        # Ensure these method names match what's in your StaticPlots class
        # and that they all accept an 'ax' parameter.
    }

    plotted_count = 0
    for i, config_item in enumerate(plot_configurations):
        if i >= len(axes_flat):
            print(f"Warning: Not enough axes for all plot configurations. Skipping config: {config_item.type}")
            break
        
        current_ax = axes_flat[i]
        plot_type = config_item.type 
        # config_item.params is a PlotParameter Pydantic model. Convert to dict for ** unpacking.
        # Exclude None values so they don't override defaults in plot methods.
        plot_params = {k: v for k, v in config_item.params.model_dump().items() if v is not None}


        if plot_type in plot_methods_map:
            plot_func = plot_methods_map[plot_type]
            try:
                # Check if all required columns for this plot type/params exist in df_to_process
                required_cols_for_plot = []
                if 'col_name' in plot_params and plot_params['col_name']: required_cols_for_plot.append(plot_params['col_name'])
                if 'col_name_x' in plot_params and plot_params['col_name_x']: required_cols_for_plot.append(plot_params['col_name_x'])
                if 'col_name_y' in plot_params and plot_params['col_name_y']: required_cols_for_plot.append(plot_params['col_name_y'])
                if 'x_col' in plot_params and plot_params['x_col']: required_cols_for_plot.append(plot_params['x_col'])
                if 'y_col' in plot_params and plot_params['y_col']: required_cols_for_plot.append(plot_params['y_col'])
                # Add more checks for hue_col, index_names_ct, column_names_ct if necessary

                missing_cols = [col for col in required_cols_for_plot if col not in df_to_process.columns]
                if missing_cols:
                    raise ValueError(f"Required column(s) for plot type '{plot_type}': {missing_cols} not found in the processed DataFrame.")

                plot_func(ax=current_ax, **plot_params)
                plotted_count += 1
            except Exception as e:
                print(f"Error plotting '{plot_type}' with params {plot_params} on axis {i}: {e}")
                current_ax.set_title(f"Plotting Error: {plot_type}", color='red', fontsize=10)
                current_ax.text(0.5, 0.5, f"Error:\n{str(e)[:100]}...", 
                                ha='center', va='center', wrap=True, color='red', fontsize=8)
        else:
            print(f"Warning: Unknown plot type '{plot_type}'. Skipping.")
            current_ax.set_title(f"Unknown plot type: {plot_type}", color='orange', fontsize=10)

    if plotted_count == 0:
        print("Warning: No plots were successfully drawn for the dashboard.")
        plt.close(fig)
        return None

    for j in range(plotted_count, len(axes_flat)): # Hide unused axes
        axes_flat[j].set_visible(False)
    
    fig.suptitle("Dashboard Plots", fontsize=16, y=1.0) # Main title for the whole figure
    try:
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    except ValueError as ve:
        print(f"Warning: plt.tight_layout() raised a ValueError: {ve}.")
    
    img_bytes = io.BytesIO()
    try:
        fig.savefig(img_bytes, format='PNG', bbox_inches='tight')
    except Exception as e:
        print(f"Error saving figure to BytesIO: {e}")
        plt.close(fig) # Ensure figure is closed on error too
        return None
    finally:
        plt.close(fig) # CRITICAL: Always close the figure
    
    img_bytes.seek(0)
    return img_bytes


def handle_generate_displot(
    base_df: pd.DataFrame,
    col_name: str,
    kind: str,
    hue_col: Optional[str] = None,
    include_columns: Optional[List[str]] = None,
    exclude_columns: Optional[List[str]] = None,
    # **kwargs for sns.displot can be passed from API if needed, via a Pydantic model for params
    **plot_specific_kwargs 
) -> Optional[io.BytesIO]:
    """
    Generates a displot image.
    Returns an io.BytesIO stream containing the PNG image, or None on error.
    """
    # For displot, the main column 'col_name' and 'hue_col' (if used)
    # must be part of the columns considered for shaping.
    # Construct effective include_columns if not provided, to ensure col_name and hue_col are considered.
    effective_include = list(include_columns) if include_columns else []
    if col_name not in effective_include:
        effective_include.append(col_name)
    if hue_col and hue_col not in effective_include:
        effective_include.append(hue_col)
    
    # If original include_columns was None, we use our generated list.
    # If it was specified, the user's selection is primary, but we need to ensure
    # col_name and hue_col are not accidentally excluded if they are using include_columns.
    # This logic can be tricky. A simpler approach is that the user *must* include
    # col_name and hue_col in their include_columns list if they use it.
    # For now, let's assume if include_columns is used, it must contain col_name/hue_col.
    
    df_to_process = get_shaped_dataframe(base_df, include_columns, exclude_columns)

    if col_name not in df_to_process.columns:
        raise ValueError(f"Column '{col_name}' for displot not found in the shaped DataFrame.")
    if hue_col and hue_col not in df_to_process.columns:
        raise ValueError(f"Hue column '{hue_col}' for displot not found in the shaped DataFrame.")
        
    if df_to_process.empty:
        print(f"Warning: DataFrame is empty after shaping for displot on '{col_name}'. No plot generated.")
        return None

    plots_instance = get_static_plots_instance(df_to_process)
    
    fig_object = None # Initialize to ensure it's defined for finally block
    try:
        # StaticPlots.dist_plot is expected to return a matplotlib.figure.Figure object
        fig_object = plots_instance.dist_plot(
            col_name=col_name, 
            kind=kind, 
            hue_col=hue_col, 
            **plot_specific_kwargs # Pass any other specific kwargs for sns.displot
        )
        
        if fig_object is None or not isinstance(fig_object, plt.Figure):
            print("Error: StaticPlots.dist_plot did not return a valid Matplotlib Figure.")
            return None # Or raise an error

        img_bytes = io.BytesIO()
        fig_object.savefig(img_bytes, format='PNG', bbox_inches='tight')
        img_bytes.seek(0)
        return img_bytes
    except Exception as e:
        print(f"Error generating displot for '{col_name}': {e}")
        # Optionally return a placeholder error image here if needed
        return None
    finally:
        if fig_object and isinstance(fig_object, plt.Figure):
            plt.close(fig_object) # CRITICAL: Close the figure from dist_plot