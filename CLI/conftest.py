"""Configuration pytest pour CLI - setup du path."""
import sys
from pathlib import Path

# Ajoute le répertoire CLI au sys.path AVANT tout import
cli_dir = Path(__file__).parent
if str(cli_dir) not in sys.path:
    sys.path.insert(0, str(cli_dir))
