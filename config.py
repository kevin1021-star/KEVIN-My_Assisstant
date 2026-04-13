import os
from pathlib import Path

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"

# Chat Service Constants
CHATS_DATA_DIR = DATABASE_DIR / "chats_data"
MAX_CHAT_HISTORY_TURNS = 15 # Maximum number of (user, assistant) exchanges to keep in context

# Ensure directories exist
os.makedirs(CHATS_DATA_DIR, exist_ok=True)