# File: football_app/shared_logic/plots_tables.py

import sys
import os

# --- Add the external 'Diamonds_Project' directory to sys.path ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
diamonds_project_path = os.path.abspath(os.path.join(
    current_script_dir, # football_app/shared_logic/
    '..',               # up to football_app/
    '..',               # up to Python/ (or the parent of football_app and Data Visualization)
    'Data Visualization',
    'Interactive Visualization with Python',
    'Diamonds_Project'
))

if diamonds_project_path not in sys.path:
    sys.path.append(diamonds_project_path)
    print(f"[DEBUG plots_tables.py] Added '{diamonds_project_path}' to sys.path for Diamonds_Project.")
else:
    print(f"[DEBUG plots_tables.py] '{diamonds_project_path}' already in sys.path for Diamonds_Project.")

# --- Now import the specific Diamonds and StaticPlots classes ---
# Initialize with placeholders in case of import failure
ImportedDiamondsClass = None
ImportedStaticPlotsClass = None

try:
    # Assumes Descriptive.py in Diamonds_Project contains the Diamonds class
    from Descriptive import Diamonds as ImportedDiamondsClassInternal
    ImportedDiamondsClass = ImportedDiamondsClassInternal

    # Assumes StaticPlots.py in Diamonds_Project contains the StaticPlots class
    from StaticPlots import StaticPlots as ImportedStaticPlotsClassInternal
    ImportedStaticPlotsClass = ImportedStaticPlotsClassInternal

    print("[DEBUG plots_tables.py] Successfully imported target classes (Diamonds, StaticPlots) from Diamonds_Project.")

except ImportError as e_import:
    print(f"[ERROR plots_tables.py] ImportError during import from Diamonds_Project: {e_import}")
    print("[ERROR plots_tables.py] This means a module (e.g., Descriptive.py, StaticPlots.py, or their dependencies like seaborn, pandas) was not found.")
except NameError as e_name:
    print(f"[ERROR plots_tables.py] NameError during import from Diamonds_Project: {e_name}")
    print("[ERROR plots_tables.py] This means a name (variable, function, class) was used before it was defined, likely *within* Descriptive.py or StaticPlots.py.")
except Exception as e_general:
    print(f"[ERROR plots_tables.py] Unexpected error during import from Diamonds_Project: {type(e_general).__name__}: {e_general}")

# Make them available for import by other modules in this project,
# using placeholders if the import failed.
if ImportedDiamondsClass is None:
    print("[WARN plots_tables.py] Using placeholder for Diamonds class due to import failure.")
    class DiamondsPlaceholder: pass
    Diamonds = DiamondsPlaceholder
else:
    Diamonds = ImportedDiamondsClass

if ImportedStaticPlotsClass is None:
    print("[WARN plots_tables.py] Using placeholder for StaticPlots class due to import failure.")
    class StaticPlotsPlaceholder: pass
    StaticPlots = StaticPlotsPlaceholder
else:
    StaticPlots = ImportedStaticPlotsClass