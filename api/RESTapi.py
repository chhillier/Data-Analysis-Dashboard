# File: football_app/api/RESTapi.py

from config_paths import Diamonds, StaticPlots

# Instantiate Diamonds. Its __init__ method loads the data
# and calls the Descriptive.__init__ via super().
diamonds_data_object = Diamonds()

# Instantiate StaticPlots. Its __init__ method loads 'diamonds.csv'
plots_object = StaticPlots()

# Now you can access the data from the Diamonds object
# The .data attribute is set by the Descriptive class's __init__
print(diamonds_data_object.data.head())

# You could also potentially use plots_object here if it's set up
# For example, if it has a method to show a plot:
# plots_object.some_plotting_method()