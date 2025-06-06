import pandas as pd
import seaborn as sns

penguins_df = sns.load_dataset('penguins')

penguins_df.to_csv('penguins.csv', index=False)