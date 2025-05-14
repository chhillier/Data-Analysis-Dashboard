# File: football_app/api/config_paths.py

import sys
import os

# --- STEP 1: Add 'football_app/' to sys.path ---
# This allows this script (config_paths.py, now in api/) to find 'shared_logic'.

# Get the absolute path of the directory where this file (config_paths.py) is located.
# This will be 'football_app/api/'.
CURRENT_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate one level up to get to 'football_app/'
PROJECT_MODULE_ROOT = os.path.abspath(os.path.join(CURRENT_CONFIG_DIR, '..'))

if PROJECT_MODULE_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_MODULE_ROOT)
    print(f"[DEBUG api/config_paths.py] Added project module root '{PROJECT_MODULE_ROOT}' to sys.path.")
else:
    print(f"[DEBUG api/config_paths.py] Project module root '{PROJECT_MODULE_ROOT}' is already in sys.path.")

# --- STEP 2: Import Descriptive and StaticPlots from shared_logic.plots_tables ---
# And make them available for other modules (like RESTapi.py) to import directly from this 'config_paths' module.

try:
    # 'shared_logic' should now be findable because PROJECT_MODULE_ROOT (football_app/) is on sys.path
    from shared_logic.plots_tables import Descriptive as _Descriptive_from_plots_tables
    from shared_logic.plots_tables import StaticPlots as _StaticPlots_from_plots_tables
    print("[DEBUG api/config_paths.py] Successfully imported classes from shared_logic.plots_tables.")

    # Re-export them so 'from config_paths import Descriptive' (from RESTapi.py) works
    Descriptive = _Descriptive_from_plots_tables
    StaticPlots = _StaticPlots_from_plots_tables

except ModuleNotFoundError as e:
    print(f"[ERROR api/config_paths.py] Could not find 'shared_logic.plots_tables': {e}")
    print(f"[ERROR api/config_paths.py] Ensure 'football_app/shared_logic/__init__.py' and 'football_app/shared_logic/plots_tables.py' exist.")
    class Descriptive: pass # Placeholder
    class StaticPlots: pass # Placeholder
except ImportError as e:
    print(f"[ERROR api/config_paths.py] Error importing from 'shared_logic.plots_tables': {e}")
    print(f"[ERROR api/config_paths.py] This likely means 'plots_tables.py' had an issue importing from Diamonds_Project.")
    class Descriptive: pass # Placeholder
    class StaticPlots: pass # Placeholder
except Exception as e:
    print(f"[ERROR api/config_paths.py] Unexpected error: {e}")
    class Descriptive: pass # Placeholder
    class StaticPlots: pass # Placeholder

# print(f"[DEBUG api/config_paths.py] Descriptive available: {type(Descriptive)}")
# print(f"[DEBUG api/config_paths.py] StaticPlots available: {type(StaticPlots)}")