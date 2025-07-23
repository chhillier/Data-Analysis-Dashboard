from descriptive import Descriptive
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import math
from typing import Optional, Union, Callable
class StaticPlots(Descriptive):
    def __init__(self, data_df: pd.DataFrame):
        super().__init__(data_df)
    def _get_estimator_name(self,est):
        if est is None: return "values"
        if isinstance(est, str): return est
        if hasattr(est, '__name__'): return est.__name__
        return str(est)

    def histogram(self, col_name: str, ax: plt.Axes, color: str = 'blue', bins: int = 20, **kwargs) -> plt.Axes:
        if col_name not in self.data.columns:
            raise ValueError(f"{col_name} not in list of features for data")

        # Extract parameters that came from the UI via kwargs
        kde_enabled = kwargs.pop('kde', False)
        statistic_type = kwargs.pop('stat', 'count') # Use the stat from UI, or default
        kde_custom_line_color = kwargs.pop('kde_line_color', None)
        remaining_hist_kwargs = kwargs.copy()

        # Your defensive popping for parameters not relevant to histplot
        remaining_hist_kwargs.pop('errorbar', None)
        remaining_hist_kwargs.pop('annot', None)
        remaining_hist_kwargs.pop('fmt', None)
        remaining_hist_kwargs.pop('cmap', None)
        remaining_hist_kwargs.pop('annot_kws', None)
        remaining_hist_kwargs.pop('index_names_ct', None)
        remaining_hist_kwargs.pop('column_names_ct', None)


        # --- Plot 1: The Histogram Bars ---
        sns.histplot(
            data=self.data,
            x=col_name,
            ax=ax,
            color=color,
            bins=bins, 
            kde=False, 
            stat=statistic_type, 
            edgecolor='black',
            **remaining_hist_kwargs
        )

    # --- Plot 2: The KDE Line (if enabled) ---
        if kde_enabled:
            if pd.api.types.is_numeric_dtype(self.data[col_name]): # Check if column is numeric
                # Determine the KDE line color
                if kde_custom_line_color:
                    final_kde_color_for_plot = kde_custom_line_color
                else: 
                    if color.lower() == '#ff5733':
                        final_kde_color_for_plot = '#1f77b4' 
                    else:
                        final_kde_color_for_plot = '#FF5733'
                
                kde_plot_linewidth = kwargs.pop('kde_linewidth', 2) 
                kde_plot_alpha = kwargs.pop('kde_alpha', 1)       

                print(f"DEBUG StaticPlots.histogram (Separate KDE): Plotting KDE for {col_name} with color='{final_kde_color_for_plot}', linewidth={kde_plot_linewidth}, alpha={kde_plot_alpha}")

                ax2 = ax.twinx()
                sns.kdeplot(
                    data=self.data,
                    x=col_name,
                    ax=ax2, # Plot on the twin axis
                    color=final_kde_color_for_plot,
                    linewidth=kde_plot_linewidth,
                    alpha=kde_plot_alpha
                )
                ax2.set_yticks([]) 
                ax2.set_ylabel('') 
            else:
                print(f"INFO StaticPlots.histogram: KDE overlay skipped for non-numeric column '{col_name}'.")
                
        ax.set_title(f"Distribution of {col_name.replace('_',' ').title()} ({statistic_type.capitalize()})", fontsize = 14)
        ax.tick_params(axis='x', rotation=45)
        return ax



    def kde(self, col_name:str, ax:int, hue_col:str=None, **kwargs):
        
        if col_name not in self.data.columns:
            raise ValueError(f"{col_name} not in list of features for data")
        ui_fill = kwargs.pop('fill', True)
        ui_alpha = kwargs.pop('alpha', 0.7)
        ui_linewidth = kwargs.pop('linewidth', 1.5)

        remaining_kde_kwargs = kwargs.copy()
        irrelevant_params = [
            'bins',             # Specific to histogram
            'errorbar',         # Specific to barplot
            'estimator',        # Specific to barplot
            'col_name_x',       # kde typically uses 'x' (our col_name) and possibly 'y'
            'col_name_y',       # if doing 2D KDE (our current method is 1D on col_name)
            'index_names_ct',   # Specific to crosstab_heatmap
            'column_names_ct',  # Specific to crosstab_heatmap
            'annot',            # Specific to heatmap (and sometimes bar_label, but not kdeplot itself)
            'fmt',              # Specific to heatmap annotation
            'cmap',             # kdeplot has 'palette' or 'color', cmap is more for heatmaps/imshow
            'annot_kws'         # Specific to heatmap
        ]
        for param in irrelevant_params:
            remaining_kde_kwargs.pop(param, None)
            print(f"DEBUG StaticPlots.kde: col_name='{col_name}', hue_col='{hue_col}', "
          f"fill={ui_fill}, alpha={ui_alpha}, linewidth={ui_linewidth}, "
          f"other_kwargs_for_kdeplot={remaining_kde_kwargs}")
        sns.kdeplot(data = self.data,
                     x= col_name,
                     ax=ax,
                     hue=hue_col,
                    fill=ui_fill,
                    alpha = ui_alpha,
                    linewidth = ui_linewidth,
                    **remaining_kde_kwargs)
        title = f"Density Estimate of {col_name.replace('_', ' ').title()}"
        if hue_col: title += f" by {hue_col.replace('_', ' ').title()}"
        ax.set_title(title, fontsize = 14)
        ax.tick_params(axis='x', rotation=45)
        return ax

    def scatter(self, 
                col_name_x: str, 
                col_name_y: str, 
                ax: plt.Axes,      # Corrected type hint for ax
                color: Optional[str] = None, # Allow None to let hue drive color, or use default
                hue_col: Optional[str] = None,
                alpha: Optional[float] = None,
                # Add other common scatterplot params you want to control from PlotParameter explicitly
                # For example: size_col: Optional[str] = None, style_col: Optional[str] = None,
                **kwargs  # Remaining kwargs from plot_params
               ) -> plt.Axes:

        if col_name_x not in self.data.columns:
            raise ValueError(f"Column '{col_name_x}' not found for scatter plot x-axis.")
        if col_name_y not in self.data.columns:
            raise ValueError(f"Column '{col_name_y}' not found for scatter plot y-axis.")
        if hue_col and hue_col not in self.data.columns:
            raise ValueError(f"Hue column '{hue_col}' not found for scatter plot.")

        scatter_plot_kwargs = kwargs.copy()
        
        # Parameters from PlotParameter that are definitely NOT for sns.scatterplot
        irrelevant_params_for_scatter = [
            'bins', 'errorbar', 'estimator', 'kind', # From other plot types
            'index_names_ct', 'column_names_ct', 'annot', 'fmt', 'cmap', 'annot_kws', # From heatmap
            'col_name' # This specific one is not used if x and y are explicit (col_name_x, col_name_y)
        ]
        for param_name in irrelevant_params_for_scatter:
            scatter_plot_kwargs.pop(param_name, None) # Remove if present

        # The named parameters (color, hue_col, alpha) will be passed explicitly.
        # If 'color' was also in plot_params and thus in kwargs, pop it to avoid conflict
        # if your method's 'color' should take precedence or if you want to handle logic.
        # However, if a parameter is named in the method signature, it won't be in kwargs.
        # So, only need to pop things from kwargs that are NOT sns.scatterplot parameters.
        
        # 's' (for marker size) is a common one for scatter, often passed via kwargs.
        # If you added 'size_col' as a named param, handle it for sns.scatterplot's 'size' argument.

        actual_color = color
        if hue_col is not None and color is not None:
            # If hue is used, seaborn typically controls colors by palette.
            # Explicitly setting color might override this, or you might want to remove it.
            print(f"Warning: Both 'color' ({color}) and 'hue_col' ({hue_col}) provided for scatter. Hue will likely determine colors.")
            actual_color = None # Let hue control palette

        print(f"DEBUG: Calling sns.scatterplot for {col_name_x} vs {col_name_y} "
              f"with color='{actual_color}', hue_col='{hue_col}', alpha='{alpha}', "
              f"other kwargs: {scatter_plot_kwargs}")

        sns.scatterplot(
            data=self.data, 
            x=col_name_x, 
            y=col_name_y, 
            ax=ax, 
            color=actual_color, # Use the method's processed color parameter
            hue=hue_col,      # Pass hue_col to sns.scatterplot's 'hue'
            alpha=alpha,      # Pass alpha directly
            **scatter_plot_kwargs # Pass filtered additional kwargs
        )
        
        title = f"{col_name_y.replace('_', ' ').title()} vs. {col_name_x.replace('_', ' ').title()}"
        if hue_col: title += f" by {hue_col.replace('_', ' ').title()}"
        ax.set_title(title, fontsize = 14)
        ax.tick_params(axis='x', rotation=45)
        return ax
            
    def count_plot(self, 
                   ax: plt.Axes, 
                   x_col: str, 
                   hue_col: Optional[str] = None, # Explicitly accept hue_col
                   color: Optional[str] = None,   # Explicitly accept color
                   **kwargs
                  ) -> plt.Axes:
        if x_col not in self.categorical_data().columns: # Ensure this method is accessible
            err_msg = f"Error: Column '{x_col}' not found or not categorical for count_plot."
            ax.set_title(err_msg, color='red')
            ax.text(0.5, 0.5, err_msg, ha='center', va='center', wrap=True, color='red')
            print(f"Error in count_plot: {err_msg}")
            return ax
        if hue_col and hue_col not in self.data.columns: # Validate hue_col if provided
             err_msg = f"Error: Hue column '{hue_col}' not found for count_plot."
             ax.set_title(err_msg, color='red')
             ax.text(0.5, 0.5, err_msg, ha='center', va='center', wrap=True, color='red')
             print(f"Error in count_plot: {err_msg}")
             return ax
        ui_palette = kwargs.pop('palette', None)
        ui_dodge = kwargs.pop('dodge', True)
        ui_alpha = kwargs.pop('alpha', 1.0)

        actual_color_for_sns = color
        if hue_col and color:
            print(f"Warning: Both 'color' ('{color}') and 'hue_col' ('{hue_col}') provided for count_plot. "
                  f"The 'palette' (if any, or default) will be used for hue differentiation. Single 'color' arg ignored.")
            actual_color_for_sns = None
        
        remaining_countplot_kwargs = kwargs.copy()
        
        # Parameters from PlotParameter not for sns.countplot (or already handled)
        irrelevant_params = [
            'bins', 'errorbar', 'estimator', 'kind', 'col_name',
            'index_names_ct', 'column_names_ct', 'annot', 'fmt', 'cmap', 'annot_kws',
            'col_name_x', 'col_name_y', 
            # 'x_col' is a named param, 'hue_col' is a named param, 'color' is a named param
        ]
        for p_name in irrelevant_params:
            remaining_countplot_kwargs.pop(p_name, None)

        try:
            sns.countplot(
                data=self.data,
                x=x_col,
                ax=ax,
                hue=hue_col,
                color=actual_color_for_sns, # Use this to allow palette to work with hue
                palette= ui_palette,
                dodge=ui_dodge,
                alpha=ui_alpha,             # Pass alpha here
                **remaining_countplot_kwargs
            )
            title = f"Count of Observations by {x_col.replace('_', ' ').title()}"
            if hue_col: title += f" (Grouped by {hue_col.replace('_', ' ').title()})"
            ax.set_title(title, fontsize = 14)
            ax.tick_params(axis='x', rotation = 45)

        except Exception as e:
            err_msg = f"Could not create count plot for {x_col} : {e}"
            ax.set_title(err_msg, color = 'red')
            ax.text(0.5,0.5, err_msg, ha= 'center', va= 'center', wrap = True, color = 'red')
            print(f"Error in count_plot: {err_msg}")
        return ax


    def bar_chart(self, 
                  ax: plt.Axes, 
                  x_col: str, 
                  y_col: Optional[str] = None,
                  hue_col: Optional[str] = None, # Parameter for the hue column name
                  estimator: Union[str, Callable, None] = 'mean',
                  errorbar: Optional[Union[str, tuple]] = ('ci', 95),
                  color: Optional[str] = None,
                  palette: Optional[str] = None,
                  saturation: Optional[float] = 0.75, # Default for sns.barplot
                  dodge: Optional[bool] = None, # Let Seaborn decide default based on hue
                  alpha: Optional[float] = None, # Opacity
                  linewidth: Optional[float] = None, # Linewidth of bar edges
                  edgecolor: Optional[str] = None, # Color of bar edges
                  **kwargs  # For any other valid kwargs for sns.barplot or matplotlib.patches.Rectangle
                 ) -> plt.Axes:

        # --- Input Validation ---
        if x_col not in self.data.columns: # Check against self.data.columns
            err_msg = f"Error: X-column '{x_col}' not found for bar_chart."
            ax.set_title(err_msg, color='red'); ax.text(0.5,0.5, err_msg, ha='center', va='center', wrap=True, color='red'); return ax
        if y_col is not None and y_col not in self.data.columns:
            err_msg = f"Error: Y-column '{y_col}' not found for bar_chart."
            ax.set_title(err_msg, color='red'); ax.text(0.5,0.5, err_msg, ha='center', va='center', wrap=True, color='red'); return ax
        if hue_col and hue_col not in self.data.columns:
             err_msg = f"Error: Hue column '{hue_col}' not found for bar_chart."
             ax.set_title(err_msg, color='red'); ax.text(0.5,0.5, err_msg, ha='center', va='center', wrap=True, color='red'); return ax
        
        # --- Prepare kwargs for sns.barplot ---
        plot_specific_kwargs = kwargs.copy()
        
        # Parameters from PlotParameter that are definitely NOT for sns.barplot or its underlying artists
        irrelevant_params = [
            'bins', 'kind', 'stat', 'element', 'kde', # hist/displot/kde specific
            'col_name', 'col_name_x', 'col_name_y', 's', 'style', # scatter/generic specific
            'index_names_ct', 'column_names_ct', 'annot', 'fmt', 'cmap', 'annot_kws', # heatmap specific
            'cbar', 'square', 'heatmap_linewidths', 'heatmap_linecolor', # heatmap specific
            'fill', 'bw_method' # kde specific
        ]
        for p_name in irrelevant_params:
            plot_specific_kwargs.pop(p_name, None) # Remove them if they exist in kwargs

        # Handle color vs. hue/palette interaction
        effective_color = color
        if hue_col and color:
            # If hue is active, palette often takes precedence over a single color.
            # Setting color to None lets Seaborn use the palette fully with hue.
            print(f"Warning: Both 'color' ({color}) and 'hue_col' ({hue_col}) provided for bar_chart. "
                  "Palette derived from hue will be used for colors.")
            effective_color = None 
        
        # Prepare title
        estimator_name = self._get_estimator_name(estimator)
        title = f"{estimator_name.capitalize()} of {y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}"
        if hue_col: title += f" (Grouped by {hue_col.replace('_', ' ').title()})"
        ax.set_title(title, fontsize = 14)
        ax.tick_params(axis='x', rotation=45) # Consider making rotation conditional or a param


        print(f"DEBUG: Calling sns.barplot for x='{x_col}', y='{y_col}', hue='{hue_col}', "
              f"estimator='{estimator}', errorbar='{errorbar}', color='{effective_color}', "
              f"palette='{palette}', saturation='{saturation}', dodge='{dodge}', "
              f"alpha='{alpha}', linewidth='{linewidth}', edgecolor='{edgecolor}', "
              f"other kwargs: {plot_specific_kwargs}")
        try:
            sns.barplot(
                data=self.data,
                x=x_col,
                y=y_col,
                hue=hue_col, # Pass hue_col to sns.barplot's 'hue'
                estimator=estimator,
                errorbar=errorbar,
                color=effective_color, # Pass explicitly managed color
                palette=palette,     # Pass explicitly managed palette
                saturation=saturation, # Pass explicitly managed saturation
                dodge=dodge if dodge is not None else (True if hue_col else False), # Sensible default for dodge with hue
                alpha=alpha,         # Pass explicitly managed alpha
                linewidth=linewidth,   # Pass explicitly managed linewidth
                edgecolor=edgecolor, # Pass explicitly managed edgecolor
                ax=ax,
                **plot_specific_kwargs # Pass any other filtered kwargs
            )
            
            
        except Exception as e:
            err_msg = f"Error generating bar chart for {x_col}: {e}"
            ax.set_title(err_msg, color='red', fontsize=10) # Smaller font for error title
            ax.text(0.5, 0.5, f"Error:\n{str(e)[:150]}...", # Truncate long errors
                    ha='center', va='center', wrap=True, color='red', fontsize=9)
            print(f"ERROR in StaticPlots.bar_chart: {err_msg}")
            import traceback
            print(traceback.format_exc()) # Print full traceback for server log
        return ax
 
    def crosstab_heatmap(self, ax: plt.Axes, index_names_ct:list, column_names_ct:list, # ax type corrected
                         normalize_ct: bool = False, margins_ct:bool = False, 
                         annot: bool = True, fmt:str = 'd', cmap: str = 'viridis', 
                         # annot_kws from PlotParameter will come in via **kwargs
                         **kwargs) -> plt.Axes: # Return type corrected
        heatmap_kwargs = kwargs.copy()
        irrelevant_params = [
            'bins', 'errorbar', 'estimator', 'kind', 'col_name', 
            'col_name_x', 'col_name_y', 'alpha', 'hue_col', 'x_col', 'y_col',
            # Named params like annot, fmt, cmap are handled by signature
            # index_names_ct, column_names_ct, normalize_ct, margins_ct are for self.cross_tabs
        ]

        for p_name in irrelevant_params:
            heatmap_kwargs.pop(p_name, None)
            
        # If 'annot_kws' is in heatmap_kwargs, it will be passed. If not, sns.heatmap uses its default.
        # This assumes 'annot_kws' is a key in your schemas.PlotParameter.params if provided.
        # Your schemas.PlotParameter has `annot_kws: Optional[Dict[str, Any]] = None` which is good.

        print(f"DEBUG: Calling sns.heatmap with annot={annot}, fmt='{fmt}', cmap='{cmap}', kwargs: {heatmap_kwargs}")
        try:
            crosstab_data = self.cross_tabs( # This is from Descriptive
                index_names = index_names_ct,
                columns_names = column_names_ct,
                normalize = normalize_ct,
                margins = margins_ct
            )

            sns.heatmap(data=crosstab_data, ax=ax, annot=annot, fmt=fmt, cmap=cmap, 
                        **heatmap_kwargs) # Pass filtered kwargs (which could include annot_kws)
   
        except Exception as e:

            print(f"Error plotting heatmap: {e}")
        ax.tick_params(axis='x', rotation=45)
        return ax
        

