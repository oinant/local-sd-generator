"""Configuration pytest et fixtures communes."""
import sys
import os
from pathlib import Path

# Ajoute le répertoire CLI au path pour les imports
cli_dir = Path(__file__).parent.parent
sys.path.insert(0, str(cli_dir))
