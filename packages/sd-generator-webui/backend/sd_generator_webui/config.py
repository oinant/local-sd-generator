import os
import json
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLI_DIR = PROJECT_ROOT / "CLI"
VARIATIONS_DIR = PROJECT_ROOT / "variations"

# Image folders configuration - Load from environment
IMAGE_FOLDERS: List[dict] = json.loads(os.getenv("IMAGE_FOLDERS"))

# Use the first configured folder as IMAGES_DIR
IMAGES_DIR = Path(IMAGE_FOLDERS[0]["path"]) if IMAGE_FOLDERS else PROJECT_ROOT / "apioutput" / "images"

# Thumbnails and metadata stored alongside for now (TODO: configure separately)
THUMBNAILS_DIR = IMAGES_DIR.parent / "thumbnails"
METADATA_DIR = IMAGES_DIR.parent / "metadata"

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_WORKERS = int(os.getenv("API_WORKERS", "1"))

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Stable Diffusion WebUI Configuration
SD_WEBUI_URL = os.getenv("SD_WEBUI_URL", "http://127.0.0.1:7860")

# Authentication - Load from environment variables
VALID_GUIDS: List[str] = json.loads(os.getenv("VALID_GUIDS"))
READ_ONLY_GUIDS: List[str] = json.loads(os.getenv("READ_ONLY_GUIDS"))

# Image Processing
MAX_IMAGES_PER_GENERATION = 10
THUMBNAIL_SIZE = (256, 256)
THUMBNAIL_QUALITY = 85

# Ensure directories exist
for directory in [IMAGES_DIR, THUMBNAILS_DIR, METADATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)