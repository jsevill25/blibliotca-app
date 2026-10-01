from pathlib import Path
import sys


APP_NAME = "Biblioteca Central Rómulo Gallegos"
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"
DATABASE_PATH = DATA_DIR / "biblioteca_central.db"

COLORS = {
    "black": "#1A1A1A",
    "yellow": "#F5C518",
    "white": "#FFFFFF",
    "gray": "#6B6B6B",
    "surface": "#F4F4F1",
    "border": "#D4D4D0",
    "success": "#247A4B",
    "danger": "#B53A32",
}

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"