from descriptive import Descriptive
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import math
from typing import Optional, Union, Callable
class StaticPlots(Descriptive):
    def __init__(self):
        diamonds_df = pd.read_csv('diamonds.csv')
        super().__init__(diamonds_df)
    def _get_estimator_name(self,est):
        if est is None: return "values"
        if isinstance(est, str): return est
        if hasattr(est, '__name__'): return est.__name__
        return str(est)
    def histogram(self,col_name:str,ax:int, color:str = 'blue', bins:int = 20, **kwargs) -> int:

        if col_name not in self.data.columns:
            raise ValueError(f"{col_name} not in list of features for data")
        sns.histplot(data=self.data,x=col_name,ax=ax,color=color, bins=bins, **kwargs)
        ax.set_title(f'Histogram of {col_name}')
        return ax
    def kde(self, col_name:str, ax:int, hue_col:str=None, **kwargs):
        
        if col_name not in self.data.columns:
            raise ValueError(f"{col_name} not in list of features for data")
        sns.kdeplot(data = self.data, x= col_name,ax=ax,hue=hue_col, fill=True, **kwargs)
        ax.set_title(f"KDE plot of {col_name}")

    def scatter(self,col_name_x:str, col_name_y:str, ax:int, color:str = 'green', **kwargs):
        if col_name_x not in self.data.columns:
            raise ValueError(f"{col_name_x} not in list of features for data")
        elif col_name_y not in self.data.columns:
            raise ValueError(f"{col_name_y} not in list of features for data")
        sns.scatterplot(data=self.data, x= col_name_x, y= col_name_y, ax=ax, **kwargs)
        ax.set_title(f"Scatterplot of {col_name_x} and {col_name_y}")
    
    def dist_plot(self,col_name:str,kind,col2, **kwargs):
            
            g = sns.displot(data=self.data,x = col_name, hue=col2, kind = kind, **kwargs) # Example displot
            g.figure.suptitle("Displot Figure (Price Per Carat by Cut)", y=1.03)
    def count_plot(self, ax, x_col:str, **kwargs) -> int:
        if x_col not in self.categorical_data().columns:
            err_msg = f"Error: {x_col} not found"
            ax.set_title(err_msg)
            ax.text(0.5,0.5, err_msg, ha='center', va='center', wrap = True)
            print(f"Error in count chart : {err_msg}")
            return ax
        try:
            sns.countplot(data=self.data,
                          x = x_col,
                          ax=ax,
                          )
            plot_title = f"Count Plot for {x_col}"
            ax.set_title(plot_title)
            ax.tick_params(axis = 'x',rotation = 45)

        except Exception as e:
            err_msg = f"Could not create count plot for {x_col}"
            ax.title(err_msg)
            ax.set_text(0.5,0.5, err_msg, ha='center', va='center, wrap=True')

        
 
    def bar_chart(self,ax, x_col:str, y_col:Optional[str]=None,
                hue: Optional[str] = None,
                estimator:Union[str,Callable,None] = 'mean',
                errorbar = ('ci',95),
                **kwargs,
                ):
        if x_col not in self.categorical_data().columns:
            err_msg = f"Error: {x_col} not found"
            ax.set_title(err_msg)
            ax.text(0.5,0.5, err_msg, ha='center', va='center', wrap = True)
            print(f"Error in bar_chart: {err_msg}")
            return ax
        if y_col is not None:
            if y_col not in self.data.columns:
                err_msg = f"Error: {y_col} not found"
                ax.set_title(err_msg)
                ax.text(0.5,0.5,err_msg, ha='center', va='center', wrap=True)
                return ax
        if hue is not None:
            if hue not in self.categorical_data().columns:
                err_msg = f"Error: {hue} not found"
                ax.set_title(err_msg)
                ax.text(0.5,0.5,err_msg, ha='center', va='center', wrap=True)
                return ax
        plot_title = f"Bar Chart: {x_col}" # Basic title
        if y_col is not None:
            plot_title += f" vs {y_col}"
        if hue is not None:
            plot_title += f" by {hue}"
        
        try:
            sns.barplot(data = self.data,
                                x = x_col,
                                y = y_col,
                                hue = hue,
                                estimator = estimator,
                                errorbar=errorbar,
                                ax=ax,
                                **kwargs,
            )
            ax.set_title(plot_title)
            ax.tick_params(axis='x', rotation=45)

        except Exception as e:
            err_msg = f"Error generating bar chart for {x_col}"
            ax.set_title(err_msg)
            ax.text(0.5,0.5, f"Error: {e}", ha='center', va='center', wrap=True)
            print(f"{err_msg}: {e}")

        return ax

    def crosstab_heatmap(self,ax, index_names_ct:list, column_names_ct:list, normalize_ct: bool = False,
                         margins_ct:bool = False, annot: bool = True, fmt:str = 'd', cmap: str = 'viridis', **kwargs):
        try:
            crosstab_data = self.cross_tabs(
                index_names = index_names_ct,
                columns_names = column_names_ct,
                normalize = normalize_ct,
                margins = margins_ct,
                
            )
        except Exception as e:
            ax.set_title(f"Error generating crosstabl")
            ax.text(0.5,0.5, f"Error: {e}", ha='center', va='center', wrap=True)
            print(f"Error in crosstab_heatmap while generating data: {e}")
            return
        
        try:
            sns.heatmap(data=crosstab_data, ax=ax, annot=annot, fmt=fmt, cmap=cmap, **kwargs)
            idx_str = ', '.join(index_names_ct)
            col_str = '. '.join(column_names_ct)
            title = f"Heatmap: {idx_str} vs {col_str}"
            if normalize_ct:
                title += " (Normalized)"
            ax.set_title(title)
            ax.tick_params(axis='x', rotation=45)
            ax.tick_params(axis='y', rotation = 0)

        except Exception as e:
            ax.set_title(f"Error plotting heatmap")
            ax.text(0.5,0.5, f"Error: {e}", ha='center', va='center', wrap=True)
            print(f"Error in crosstab_heatmap while plotting : {e}")
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
    plots = StaticPlots()
    df = plots.data

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
    plots.dist_plot(col_name='price',kind='hist',col2='cut')
    plt.show()

