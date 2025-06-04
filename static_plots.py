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


    # def histogram(self, col_name:str, ax: plt.Axes, color:str = 'blue', bins:int = 20, **kwargs) -> plt.Axes: # Ensure plt is imported
    #     if col_name not in self.data.columns:
    #         raise ValueError(f"{col_name} not in list of features for data")

    #     kde_enabled = kwargs.pop('kde', False)
    #     statistic_type = kwargs.pop('stat', 'count')
    #     kde_custom_line_color = kwargs.pop('kde_line_color', None)
    #     edge_color_from_kwargs = kwargs.pop('edgecolor', None)

    #     # Create a copy of kwargs to modify, or be selective
    #     remaining_kwargs = kwargs.copy()

    #     # sns.histplot does not accept 'errorbar'. Remove it if present.
    #     # Also remove other params from PlotParameter that are not for histplot.
    #     # For simplicity, let's just pop 'errorbar' for now.
    #     # A more robust way would be to define EXACTLY which kwargs histplot can take from PlotParameter.
    #     remaining_kwargs.pop('errorbar', None) # Remove 'errorbar' if it exists, do nothing if not
    #     remaining_kwargs.pop('annot', None)    # <<< ADD THIS LINE
    #     remaining_kwargs.pop('fmt', None)      # Also for heatmaps
    #     remaining_kwargs.pop('cmap', None)     # Also for heatmaps
    #     remaining_kwargs.pop('annot_kws', None) # Also for heatmaps
    #     remaining_kwargs.pop('index_names_ct', None) # Also for heatmaps
    #     remaining_kwargs.pop('column_names_ct', None)# Also for heatmaps
        
    #     current_line_kws = {}
    #     if kde_enabled and kde_custom_line_color:
    #         current_line_kws['color'] = kde_custom_line_color
    #     current_line_kws['linewidth'] = 2
    #     current_line_kws['alpha'] = 1

    #     print(f"DEBUG StaticPlots.histogram: col_name='{col_name}', bar_color='{color}', bins={bins}, "
    #       f"kde_enabled={kde_enabled}, statistic_type='{statistic_type}', "
    #       f"kde_line_color='{kde_custom_line_color}', "
    #       f"final_kde_kws={current_line_kws if kde_enabled and current_line_kws else None}, "
    #       f"remaining_kwargs_for_histplot={remaining_kwargs}")

    #     sns.histplot(
    #         data=self.data,
    #         x=col_name,
    #         ax=ax,
    #         color=color, 
    #         bins=bins,
    #         kde = False,
    #         line_kws=current_line_kws if kde_enabled and current_line_kws else None, 
    #         **remaining_kwargs # Pass the filtered kwargs
    #     )
    #     if kde_enabled:
    #     # Determine the KDE line color
    #         final_kde_color = kde_custom_line_color  # Use the color from UI if provided
    #         if not final_kde_color: # If no custom color from UI, pick a default distinct from bar color
    #             if color.lower() == '#ff5733': # Example: if bar color is orange
    #                 final_kde_color = '#1f77b4' # Make KDE blue
    #             else:
    #                 final_kde_color = '#FF5733' # Default KDE to orange
    #     if statistic_type in ['count', 'frequency']:
    #         ax2 = ax.twinx()  # Create a second y-axis for KDE
    #         sns.kdeplot(
    #             data=self.data,
    #             x=col_name,
    #             ax=ax2, # Plot on the twin axis
    #             color=final_kde_color,
    #             linewidth=2, # Or get from UI if you add this to schema/UI
    #             alpha=1      # Or get from UI
    #         )
    #         ax2.set_yticks([]) # Optionally hide the secondary y-axis ticks
    #         ax2.set_ylabel('') # Optionally hide the secondary y-axis label
    #     else: # For 'density', 'probability', KDE can share the same y-axis
    #         sns.kdeplot(
    #             data=self.data,
    #             x=col_name,
    #             ax=ax, # Plot on the same axis
    #             color=final_kde_color,
    #             linewidth=2,
    #             alpha=1
    #         )
      
    #     ax.set_title(f'Histogram of {col_name}')
    #     return ax

    # In static_plots.py

    def histogram(self, col_name: str, ax: plt.Axes, color: str = 'blue', bins: int = 20, **kwargs) -> plt.Axes:
        if col_name not in self.data.columns:
            raise ValueError(f"{col_name} not in list of features for data")

        # Extract parameters that came from the UI via kwargs
        kde_enabled = kwargs.pop('kde', False)
        statistic_type = kwargs.pop('stat', 'count') # Use the stat from UI, or default
        kde_custom_line_color = kwargs.pop('kde_line_color', None)
        # edge_color_from_kwargs = kwargs.pop('edgecolor', None) # For histplot bars

        # remaining_kwargs now holds any other parameters (like your defensive pops will remove from this)
        remaining_hist_kwargs = kwargs.copy()

        # Your defensive popping for parameters not relevant to histplot
        remaining_hist_kwargs.pop('errorbar', None)
        remaining_hist_kwargs.pop('annot', None)
        remaining_hist_kwargs.pop('fmt', None)
        remaining_hist_kwargs.pop('cmap', None)
        remaining_hist_kwargs.pop('annot_kws', None)
        remaining_hist_kwargs.pop('index_names_ct', None)
        remaining_hist_kwargs.pop('column_names_ct', None)
        # Consider popping other plot-specific params if they could be in kwargs:
        # e.g. 'x_col', 'y_col', 'col_name_x', 'col_name_y', 'estimator', 's', 
        # 'fill', 'linewidth_kde_specific', 'dodge', 'kind' (if you named kde linewidth differently)

        # --- Plot 1: The Histogram Bars ---
        sns.histplot(
            data=self.data,
            x=col_name,
            ax=ax,
            color=color,  # Bar color from UI (passed as named arg)
            bins=bins,    # Bins from UI (passed as named arg)
            kde=False,    # IMPORTANT: We will draw KDE separately if enabled
            stat=statistic_type, # Use the statistic type from UI
            edgecolor='black', # Use edgecolor from UI if provided
            **remaining_hist_kwargs
        )

        # --- Plot 2: The KDE Line (if enabled) ---
        if kde_enabled:
            # Determine the KDE line color
            # Use the custom color if provided, otherwise pick a default distinct from bar color
            if kde_custom_line_color:
                final_kde_color_for_plot = kde_custom_line_color
            else: # Default KDE line color logic if not specified by user
                if color.lower() == '#ff5733':  # If bar color is default orange
                    final_kde_color_for_plot = '#1f77b4'  # Make KDE blue
                else:
                    final_kde_color_for_plot = '#FF5733'  # Default KDE to orange

            # Get other KDE styling parameters (these are hardcoded for now, but could come from UI/kwargs)
            kde_linewidth = kwargs.pop('kde_linewidth', 2) # Example if you add this to schema later
            kde_alpha = kwargs.pop('kde_alpha', 1)       # Example if you add this to schema later

            # Debug print specifically for when KDE is plotted
            print(f"DEBUG StaticPlots.histogram (Separate KDE): Plotting KDE for {col_name} with color='{final_kde_color_for_plot}', linewidth={kde_linewidth}, alpha={kde_alpha}")

            # Handle y-axis scaling for KDE based on histogram's statistic
            if statistic_type in ['count', 'frequency']:
                # For count/frequency histograms, KDE (density) needs its own scale.
                # Plot on a twin axis.
                ax2 = ax.twinx()
                sns.kdeplot(
                    data=self.data,
                    x=col_name,
                    ax=ax2,
                    color=final_kde_color_for_plot,
                    linewidth=kde_linewidth,
                    alpha=kde_alpha
                )
                ax2.set_yticks([])  # Hide secondary y-axis ticks
                ax2.set_ylabel('')  # Hide secondary y-axis label
            else: # For 'density' or 'probability', KDE can share the primary y-axis
                sns.kdeplot(
                    data=self.data,
                    x=col_name,
                    ax=ax,
                    color=final_kde_color_for_plot,
                    linewidth=kde_linewidth,
                    alpha=kde_alpha
                )
                
        ax.set_title(f'Histogram of {col_name}')
        return ax


    def kde(self, col_name:str, ax:int, hue_col:str=None, **kwargs):
        
        if col_name not in self.data.columns:
            raise ValueError(f"{col_name} not in list of features for data")
        kde_plot_kwargs = kwargs.copy()
        irrelevant_params_for_kde = [
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
        for param in irrelevant_params_for_kde:
            kde_plot_kwargs.pop(param, None)
        sns.kdeplot(data = self.data, x= col_name,ax=ax,hue=hue_col, fill=True, **kde_plot_kwargs)
        ax.set_title(f"KDE plot of {col_name}")

    # def scatter(self,col_name_x:str, col_name_y:str, ax:int, color:str = 'green', **kwargs):
    #     if col_name_x not in self.data.columns:
    #         raise ValueError(f"{col_name_x} not in list of features for data")
    #     elif col_name_y not in self.data.columns:
    #         raise ValueError(f"{col_name_y} not in list of features for data")
    #     sns.scatterplot(data=self.data, x= col_name_x, y= col_name_y, ax=ax, **kwargs)
    #     ax.set_title(f"Scatterplot of {col_name_x} and {col_name_y}")

    # In static_plots.py, within the StaticPlots class
# Ensure these imports are at the top of your static_plots.py file:
# import matplotlib.pyplot as plt
# from typing import Optional 
# (pandas, seaborn, math, Descriptive, Union, Callable, List, Dict, Any should already be there)

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
        # Add similar checks for size_col, style_col if you add them

        # These are kwargs from plot_params that didn't match named args of this scatter method.
        # Filter them to only include what sns.scatterplot might accept in its own **kwargs
        # (which are typically passed to matplotlib.collections.PathCollection, e.g., 's', 'marker', 'linewidth')
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
        
        title = f"Scatterplot of {col_name_x} and {col_name_y}"
        if hue_col:
            title += f" by {hue_col}"
        ax.set_title(title)
        return ax
    
    def dist_plot(self,
                  col_name:str,
                  kind,
                  hue_col: Optional[str] = None,
                  **kwargs,
    ) -> plt.Figure:
        g = sns.displot(
            data = self.data,
            x = col_name,
            hue= hue_col,
            kind= kind,
            **kwargs
        )
        title = f"Distribution Plot of '{col_name}' (Kind :{kind})"
        if hue_col:
            title += f" by '{hue_col}'"
        g.figure.suptitle(title, y=1.03)
        return g.figure
            
    # def count_plot(self, ax, x_col:str, **kwargs) -> int:
    #     if x_col not in self.categorical_data().columns:
    #         err_msg = f"Error: {x_col} not found"
    #         ax.set_title(err_msg)
    #         ax.text(0.5,0.5, err_msg, ha='center', va='center', wrap = True)
    #         print(f"Error in count chart : {err_msg}")
    #         return ax
    #     try:
    #         sns.countplot(data=self.data,
    #                       x = x_col,
    #                       ax=ax,
    #                       )
    #         plot_title = f"Count Plot for {x_col}"
    #         ax.set_title(plot_title)
    #         ax.tick_params(axis = 'x',rotation = 45)

    #     except Exception as e:
    #         err_msg = f"Could not create count plot for {x_col}"
    #         ax.title(err_msg)
    #         ax.set_text(0.5,0.5, err_msg, ha='center', va='center, wrap=True')
    # In static_plots.py, within StaticPlots class
# Ensure: import matplotlib.pyplot as plt; from typing import Optional
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
        
        plot_specific_kwargs = kwargs.copy()
        
        # Parameters from PlotParameter not for sns.countplot (or already handled)
        irrelevant_params = [
            'bins', 'errorbar', 'estimator', 'kind', 'col_name',
            'index_names_ct', 'column_names_ct', 'annot', 'fmt', 'cmap', 'annot_kws',
            'col_name_x', 'col_name_y', 'alpha', 
            # 'x_col' is a named param, 'hue_col' is a named param, 'color' is a named param
        ]
        for p_name in irrelevant_params:
            plot_specific_kwargs.pop(p_name, None)

        actual_color = color
        if hue_col and color:
            print(f"Warning: Both 'color' and 'hue_col' provided for count_plot. Hue will likely determine colors via palette.")
            actual_color = None # Let hue and palette control

        print(f"DEBUG: Calling sns.countplot for {x_col} with hue_col '{hue_col}', color '{actual_color}', kwargs: {plot_specific_kwargs}")
        try:
            sns.countplot(
                data=self.data,
                x=x_col,
                hue=hue_col, # Pass hue_col to sns.countplot's 'hue'
                color=actual_color, # Pass color
                ax=ax,
                **plot_specific_kwargs # Pass filtered additional kwargs
            )
            plot_title = f"Count Plot for {x_col}"
            if hue_col:
                plot_title += f" by {hue_col}"
            ax.set_title(plot_title)
            ax.tick_params(axis='x', rotation=45)
        except Exception as e:
            err_msg = f"Could not create count plot for {x_col}: {e}"
            ax.set_title(err_msg, color='red')
            ax.text(0.5, 0.5, err_msg, ha='center', va='center', wrap=True, color='red')
            print(f"Error in count_plot: {err_msg}")
        return ax

        
 
    # def bar_chart(self,ax, x_col:str, y_col:Optional[str]=None,
    #             hue: Optional[str] = None,
    #             estimator:Union[str,Callable,None] = 'mean',
    #             errorbar = ('ci',95),
    #             **kwargs,
    #             ):
    #     if x_col not in self.categorical_data().columns:
    #         err_msg = f"Error: {x_col} not found"
    #         ax.set_title(err_msg)
    #         ax.text(0.5,0.5, err_msg, ha='center', va='center', wrap = True)
    #         print(f"Error in bar_chart: {err_msg}")
    #         return ax
    #     if y_col is not None:
    #         if y_col not in self.data.columns:
    #             err_msg = f"Error: {y_col} not found"
    #             ax.set_title(err_msg)
    #             ax.text(0.5,0.5,err_msg, ha='center', va='center', wrap=True)
    #             return ax
    #     if hue is not None:
    #         if hue not in self.categorical_data().columns:
    #             err_msg = f"Error: {hue} not found"
    #             ax.set_title(err_msg)
    #             ax.text(0.5,0.5,err_msg, ha='center', va='center', wrap=True)
    #             return ax
    #     plot_title = f"Bar Chart: {x_col}" # Basic title
    #     if y_col is not None:
    #         plot_title += f" vs {y_col}"
    #     if hue is not None:
    #         plot_title += f" by {hue}"
        
    #     try:
    #         sns.barplot(data = self.data,
    #                             x = x_col,
    #                             y = y_col,
    #                             hue = hue,
    #                             estimator = estimator,
    #                             errorbar=errorbar,
    #                             ax=ax,
    #                             **kwargs,
    #         )
    #         ax.set_title(plot_title)
    #         ax.tick_params(axis='x', rotation=45)

    #     except Exception as e:
    #         err_msg = f"Error generating bar chart for {x_col}"
    #         ax.set_title(err_msg)
    #         ax.text(0.5,0.5, f"Error: {e}", ha='center', va='center', wrap=True)
    #         print(f"{err_msg}: {e}")

    #     return ax
    
    # In static_plots.py, within StaticPlots class
# In your static_plots.py, within the StaticPlots class:

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
        plot_title = f"Bar Chart: {x_col}" 
        if y_col:
            plot_title += f" vs {y_col}"
        if hue_col:
            plot_title += f" by {hue_col}"
        if estimator and y_col: # Add estimator info if y_col is present
            estimator_name = self._get_estimator_name(estimator) # Use your helper
            plot_title += f" ({estimator_name} of {y_col})"


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
            ax.set_title(plot_title)
            ax.tick_params(axis='x', rotation=45) # Consider making rotation conditional or a param
        except Exception as e:
            err_msg = f"Error generating bar chart for {x_col}: {e}"
            ax.set_title(err_msg, color='red', fontsize=10) # Smaller font for error title
            ax.text(0.5, 0.5, f"Error:\n{str(e)[:150]}...", # Truncate long errors
                    ha='center', va='center', wrap=True, color='red', fontsize=9)
            print(f"ERROR in StaticPlots.bar_chart: {err_msg}")
            import traceback
            print(traceback.format_exc()) # Print full traceback for server log
        return ax
    # def crosstab_heatmap(self,ax, index_names_ct:list, column_names_ct:list, normalize_ct: bool = False,
    #                      margins_ct:bool = False, annot: bool = True, fmt:str = 'd', cmap: str = 'viridis', **kwargs):
    #     try:
    #         crosstab_data = self.cross_tabs(
    #             index_names = index_names_ct,
    #             columns_names = column_names_ct,
    #             normalize = normalize_ct,
    #             margins = margins_ct,
                
    #         )
    #     except Exception as e:
    #         ax.set_title(f"Error generating crosstabl")
    #         ax.text(0.5,0.5, f"Error: {e}", ha='center', va='center', wrap=True)
    #         print(f"Error in crosstab_heatmap while generating data: {e}")
    #         return
        
    #     try:
    #         sns.heatmap(data=crosstab_data, ax=ax, annot=annot, fmt=fmt, cmap=cmap, **kwargs)
    #         idx_str = ', '.join(index_names_ct)
    #         col_str = '. '.join(column_names_ct)
    #         title = f"Heatmap: {idx_str} vs {col_str}"
    #         if normalize_ct:
    #             title += " (Normalized)"
    #         ax.set_title(title)
    #         ax.tick_params(axis='x', rotation=45)
    #         ax.tick_params(axis='y', rotation = 0)

    #     except Exception as e:
    #         ax.set_title(f"Error plotting heatmap")
    #         ax.text(0.5,0.5, f"Error: {e}", ha='center', va='center', wrap=True)
    #         print(f"Error in crosstab_heatmap while plotting : {e}")

    #     return ax
    
    # In static_plots.py, within StaticPlots class
    def crosstab_heatmap(self, ax: plt.Axes, index_names_ct:list, column_names_ct:list, # ax type corrected
                         normalize_ct: bool = False, margins_ct:bool = False, 
                         annot: bool = True, fmt:str = 'd', cmap: str = 'viridis', 
                         # annot_kws from PlotParameter will come in via **kwargs
                         **kwargs) -> plt.Axes: # Return type corrected
        # ... (your existing try-except for data generation) ...
        # crosstab_data = self.cross_tabs(...)
        
        # Filter kwargs for sns.heatmap
        heatmap_kwargs = kwargs.copy()
        irrelevant_params = [
            'bins', 'errorbar', 'estimator', 'kind', 'col_name', 
            'col_name_x', 'col_name_y', 'alpha', 'hue_col', 'x_col', 'y_col',
            # Named params like annot, fmt, cmap are handled by signature
            # index_names_ct, column_names_ct, normalize_ct, margins_ct are for self.cross_tabs
        ]
        # annot_kws is a valid kwarg for sns.heatmap, so it should NOT be popped if present in kwargs
        # We should pop things that are definitely not for heatmap.
        for p_name in irrelevant_params:
            heatmap_kwargs.pop(p_name, None)
            
        # If 'annot_kws' is in heatmap_kwargs, it will be passed. If not, sns.heatmap uses its default.
        # This assumes 'annot_kws' is a key in your schemas.PlotParameter.params if provided.
        # Your schemas.PlotParameter has `annot_kws: Optional[Dict[str, Any]] = None` which is good.

        print(f"DEBUG: Calling sns.heatmap with annot={annot}, fmt='{fmt}', cmap='{cmap}', kwargs: {heatmap_kwargs}")
        try:
            # ... (your existing data generation for crosstab_data) ...
            # (Make sure this block is also within a try if crosstabs can fail)
            crosstab_data = self.cross_tabs( # This is from Descriptive
                index_names = index_names_ct,
                columns_names = column_names_ct,
                normalize = normalize_ct,
                margins = margins_ct
            )

            sns.heatmap(data=crosstab_data, ax=ax, annot=annot, fmt=fmt, cmap=cmap, 
                        **heatmap_kwargs) # Pass filtered kwargs (which could include annot_kws)
            # ... (your existing title and tick_params logic) ...
        except Exception as e:
            # ... (your existing exception handling for plotting) ...
            print(f"Error plotting heatmap: {e}")
        return ax
        
    def subplots(self, plot_configs, nrows=None, ncols=None, figsize=(12, 8), main_title="Data Exploration Subplots"):
        """
        Creates a figure with subplots based on a list of plot configurations.

        Args:
            plot_configs (list): List of dicts. Each dict needs:
                                 'type': str ('histogram', 'kde', 'scatter', etc.)
                                 'params': dict (parameters for the plot function,
                                           excluding 'ax' which is handled internally)
            nrows (int, optional): Number of rows. Auto-calculated if None.
            ncols (int, optional): Number of columns. Auto-calculated if None.
            figsize (tuple): Size of the entire figure.
            main_title (str): Title for the entire figure.
        """
        num_plots = len(plot_configs)
        if num_plots == 0:
            print("Warning: No plot configurations provided.")
            return

        # --- Determine grid size ---
        if nrows is None and ncols is None:
            # Auto-calculate a squarish grid
            ncols = math.ceil(math.sqrt(num_plots))
            nrows = math.ceil(num_plots / ncols)
        elif nrows is None:
            nrows = math.ceil(num_plots / ncols)
        elif ncols is None:
            ncols = math.ceil(num_plots / nrows)

        if num_plots > nrows * ncols:
             print(f"Warning: Grid size ({nrows}x{ncols}) is too small for {num_plots} plots. Some plots may be omitted or grid might be suboptimal.")
             # Adjust grid to fit all plots? For now, we proceed and rely on index checks.
             # ncols = math.ceil(num_plots / nrows) # Example adjustment if nrows is fixed

        # --- Create Figure and Axes ---
        # squeeze=False ensures axes is always a 2D numpy array, even if 1x1, 1xN, Nx1
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, squeeze=False)

        # Flatten axes array for easy sequential access
        axes_flat = axes.flatten()

        # --- Map plot types to methods ---
        plot_methods = {
            'histogram': self.histogram,
            'kde': self.kde,
            'scatter': self.scatter,
            'crosstab_heatmap': self.crosstab_heatmap,
            'bar_chart': self.bar_chart,
            'count_plot': self.count_plot
            # Add more plot types and corresponding methods here
        }

        # --- Iterate through configs and plot ---
        for i, config in enumerate(plot_configs):
            if i >= len(axes_flat):
                print(f"Warning: Ran out of subplot axes. Skipping config {i+1}: {config}")
                break # Stop if we have more plots than axes

            current_ax = axes_flat[i]
            plot_type = config.get('type')
            params = config.get('params', {})

            if plot_type in plot_methods:
                plot_func = plot_methods[plot_type]
                try:
                    # Call the appropriate plotting method with the current axis
                    # and unpack the parameters from the config dictionary
                    plot_func(ax=current_ax, **params)
                except Exception as e:
                    print(f"Error plotting '{plot_type}' with params {params} on axis {i}: {e}")
                    current_ax.set_title(f"Plotting Error!") # Show error on the subplot
            else:
                print(f"Warning: Unknown plot type '{plot_type}' in config {i+1}. Skipping.")
                current_ax.set_title(f"Unknown type: {plot_type}")

        # --- Clean up and Display ---
        # Hide any unused axes in the grid
        for j in range(i + 1, len(axes_flat)):
            axes_flat[j].set_visible(False)

        if main_title:
            fig.suptitle(main_title, fontsize=16, y=1.0) # Adjust y based on layout

        # Adjust layout - rect helps prevent suptitle overlapping axes titles
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        plt.show()



if __name__ == "__main__":
    from api_data_manager import CSVDataManager
    instance_of_data = CSVDataManager(file_path="diamonds.csv")
    instance_of_data.load_and_prepare_data()
    df = instance_of_data.get_processed_df()
    plots = StaticPlots(data_df=df)

    # --- DATA INSPECTION FOR 'cut' COLUMN (using your 'df' variable) ---
    print("\n--- DATA INSPECTION FOR 'cut' COLUMN ---")
    if 'cut' in df.columns: # Using your 'df'
        print(f"Data type of 'cut': {df['cut'].dtype}")
        print(f"First 5 values of 'cut':\n{df['cut'].head().to_string()}")
        print(f"Value counts for 'cut' (includes NaNs if any):\n{df['cut'].value_counts(dropna=False).to_string()}")
        print(f"Number of NaNs in 'cut': {df['cut'].isnull().sum()}")
        print(f"Total non-NaN values in 'cut': {df['cut'].count()}")
        print(f"Is the 'cut' column (non-NaN) empty? {df['cut'].dropna().empty}")
        print(f"Shape of the entire DataFrame: {df.shape}")
    else:
        print("Error: 'cut' column not found in the DataFrame!")
    print("--- END OF DATA INSPECTION ---\n")

    plot_configurations = [
    {
        'type': 'histogram',
        'params': {'col_name': 'carat', 'color': 'teal', 'bins': 30}
    },
    {
        'type': 'kde',
        'params': {'col_name': 'price', 'hue_col':'cut'}
    },
    {
        'type': 'scatter',
        'params': {'col_name_x': 'carat', 'col_name_y': 'price', 'color': 'darkorange', 'alpha': 0.1} # Low alpha for dense scatter
    },

    {
            'type': 'crosstab_heatmap',  # Your new plot type
            'params': {
                'index_names_ct': ['cut'],                # Params for self.cross_tabs
                'column_names_ct': ['clarity', 'color'], # Params for self.cross_tabs
                'annot': False,                           # Param for sns.heatmap
                'fmt': 'd',                              # Param for sns.heatmap
                'annot_kws':{'size':7}                       # Param for sns.heatmap
                # You can add other heatmap_kwargs here, e.g., linewidths=0.5
        },
    },
    # For a bar chart of mean price by cut:
    {
        'type': 'bar_chart',
        'params': {'x_col': 'cut', 'y_col': 'price', 'estimator': 'mean', 'hue': 'color'}
    },
    # For a count plot of cut:
    {
        'type': 'count_plot',
        'params': {'x_col': 'cut'} # y_col is None by default
    },
    # Add more plot dictionaries here for more subplots
    ]
    plots.subplots(plot_configurations,
                   figsize=(18,10))
    plots.dist_plot(col_name='price',kind='hist',hue_col='cut')
    plt.show()

