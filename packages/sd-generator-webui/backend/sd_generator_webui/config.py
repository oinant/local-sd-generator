import os
import json
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file (optional)
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLI_DIR = PROJECT_ROOT / "CLI"
VARIATIONS_DIR = PROJECT_ROOT / "variations"


def load_global_config() -> dict:
    """
    Load sdgen_config.json from configured path or current working directory.

    Priority:
    1. SDGEN_CONFIG_PATH env var (set by CLI when launching backend)
    2. Current working directory (fallback for standalone usage)

    Returns:
        Config dictionary with defaults if file not found
    """
    # Try to get config path from environment (set by CLI)
    config_path_str = os.getenv("SDGEN_CONFIG_PATH")
    if config_path_str:
        config_path = Path(config_path_str)
    else:
        # Fallback to current working directory
        config_path = Path.cwd() / "sdgen_config.json"

    if not config_path.exists():
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


# Load global config for webui_token
GLOBAL_CONFIG = load_global_config()

# Image folders configuration - Load from environment or use default
IMAGE_FOLDERS_STR = os.getenv("IMAGE_FOLDERS", '[{"name": "Default", "path": "/mnt/d/StableDiffusion/apioutput"}]')
IMAGE_FOLDERS: List[dict] = json.loads(IMAGE_FOLDERS_STR)

# Use the first configured folder as IMAGES_DIR
IMAGES_DIR = Path(IMAGE_FOLDERS[0]["path"]) if IMAGE_FOLDERS else PROJECT_ROOT / "apioutput" / "images"

# Thumbnails and metadata stored alongside for now (TODO: configure separately)
THUMBNAILS_DIR = IMAGES_DIR.parent / "thumbnails"
METADATA_DIR = IMAGES_DIR.parent / "metadata"

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_WORKERS = int(os.getenv("API_WORKERS", "1"))

# Stable Diffusion WebUI Configuration
SD_WEBUI_URL = GLOBAL_CONFIG.get("api_url", os.getenv("SD_WEBUI_URL", "http://127.0.0.1:7860"))

# Authentication - Load from sdgen_config.json or .env fallback
webui_token: Optional[str] = GLOBAL_CONFIG.get("webui_token")

if webui_token:
    # Token configured in sdgen_config.json - use it
    VALID_GUIDS: List[str] = [webui_token]
    READ_ONLY_GUIDS: List[str] = []
else:
    # Fallback to .env for backward compatibility
    valid_guids_str = os.getenv("VALID_GUIDS", "[]")
    read_only_guids_str = os.getenv("READ_ONLY_GUIDS", "[]")
    VALID_GUIDS = json.loads(valid_guids_str)
    READ_ONLY_GUIDS = json.loads(read_only_guids_str)

# Image Processing
MAX_IMAGES_PER_GENERATION = 10
THUMBNAIL_SIZE = (256, 256)
THUMBNAIL_QUALITY = 85

# Ensure directories exist
for directory in [IMAGES_DIR, THUMBNAILS_DIR, METADATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)