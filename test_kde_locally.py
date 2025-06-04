# test_kde_locally.py
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np # for np.where, though we can simplify
import traceback

print(f"Seaborn version: {sns.__version__}")
print(f"Pandas version: {pd.__version__}")
print(f"Matplotlib version: {plt.matplotlib.__version__}")

try:
    # Load the data (mirroring your DataManager)
    df = pd.read_csv("diamonds.csv")

    # Apply similar post-processing as in your DataManager's _post_process_data
    # This is just to ensure the 'price' column is in a similar state
    if 'price' in df.columns and 'carat' in df.columns:
        # Ensure carat is not zero to avoid division by zero if that check is important
        # For simplicity, let's assume carat is positive as in standard diamonds dataset
        df['price_per_carat'] = round(df['price'] / df['carat'], 2) 
    
    if 'price_per_carat' in df.columns:
        # Simplified high_price logic for testing
        df["high_price"] = np.where(df['price_per_carat'] > 3500, 1, 0) 

    print(f"\nData for 'price' column (first 5 values): \n{df['price'].head()}")
    print(f"Number of NaN values in 'price': {df['price'].isnull().sum()}")
    print(f"Number of unique values in 'price': {df['price'].nunique()}")
    print(f"Min price: {df['price'].min()}, Max price: {df['price'].max()}")


    fig, ax = plt.subplots()

    # These are the exact parameters from your last successful debug log
    col_name = 'price'
    bar_color = '#1f77b4'
    bins_count = 30
    kde_is_enabled = True
    stat_type = 'count'
    kde_plot_kws = {'color': '#FF5733', 'linewidth': 2, 'alpha': 1}
    # remaining_histplot_kwargs would be any other direct histplot params, empty in your case

    print(f"\nAttempting sns.histplot with: x='{col_name}', color='{bar_color}', bins={bins_count}, kde={kde_is_enabled}, stat='{stat_type}', kde_kws={kde_plot_kws}")

    sns.histplot(
        data=df,
        x=col_name,
        ax=ax,
        color=bar_color,
        bins=bins_count,
        kde=kde_is_enabled,
        stat=stat_type,
        kde_kws=kde_plot_kws
        # **remaining_histplot_kwargs (empty in your debug log)
    )
    
    ax.set_title(f"Minimal Test: Histogram of {col_name} with KDE")
    
    # Save the plot to a file to inspect it
    output_filename = "kde_test_output.png"
    plt.savefig(output_filename)
    print(f"\nPlot saved to {output_filename}")
    plt.show() # Also try to show it if your local environment supports GUI

except FileNotFoundError:
    print("ERROR: diamonds.csv not found. Make sure it's in the same directory as test_kde_locally.py")
except Exception as e:
    print(f"An error occurred: {e}")
    traceback.print_exc()