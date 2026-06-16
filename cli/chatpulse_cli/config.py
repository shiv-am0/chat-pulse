import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".chatpulse"
DEFAULT_API_URL = "http://localhost:8000/api"
DEFAULT_POLL_INTERVAL = 2


def get_api_url() -> str:
    return os.environ.get("CHATPULSE_API_URL") or DEFAULT_API_URL


def get_poll_interval() -> int:
    val = os.environ.get("CHATPULSE_POLL_INTERVAL")
    return int(val) if val else DEFAULT_POLL_INTERVAL
