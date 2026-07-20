import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.resolve()

load_dotenv(dotenv_path=BASE_DIR / ".env")

SSH_USERNAME = "root"
SSH_KEY_PATH = str(BASE_DIR / ".ssh" / "frr_automation")

ROUTERS = [
    {"name": "R1", "host": "192.168.99.1", "config_file": str(BASE_DIR / "configs" / "r1.conf")},
    {"name": "R2", "host": "192.168.99.2", "config_file": str(BASE_DIR / "configs" / "r2.conf")},
    {"name": "R3", "host": "192.168.99.3", "config_file": str(BASE_DIR / "configs" / "r3.conf")},
]

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "network_lab",
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite"
