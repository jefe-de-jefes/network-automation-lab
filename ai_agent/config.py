import os
from dotenv import load_dotenv

load_dotenv()

SSH_USERNAME = "root"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SSH_KEY_PATH = os.path.join(BASE_DIR, "..", ".ssh", "frr_automation")

ROUTERS = [
    {"name": "R1", "host": "192.168.99.1"},
    {"name": "R2", "host": "192.168.99.2"},
    {"name": "R3", "host": "192.168.99.3"},
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
