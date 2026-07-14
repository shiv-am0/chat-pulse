import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".chatpulse"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_API_URL = "https://api.chatpulse.online/api"
DEFAULT_POLL_INTERVAL = 2


def _ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_config() -> dict:
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_config(config: dict):
    _ensure_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)


def get_api_url() -> str:
    env_url = os.environ.get("CHATPULSE_API_URL")
    if env_url:
        return env_url
    config = _load_config()
    return config.get("api_url") or DEFAULT_API_URL


def set_api_url(url: str):
    config = _load_config()
    config["api_url"] = url
    _save_config(config)


def unset_api_url():
    config = _load_config()
    config.pop("api_url", None)
    _save_config(config)


def get_poll_interval() -> int:
    val = os.environ.get("CHATPULSE_POLL_INTERVAL")
    return int(val) if val else DEFAULT_POLL_INTERVAL
