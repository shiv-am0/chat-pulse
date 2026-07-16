import json
import os
import hashlib
from pathlib import Path
from .config import CONFIG_DIR


def _token_suffix() -> str:
    """Hash the current terminal device to isolate tokens per TTY."""
    try:
        tty = os.ttyname(0)
    except (OSError, AttributeError):
        tty = "default"
    return hashlib.md5(tty.encode()).hexdigest()[:8]


def _token_path() -> Path:
    return CONFIG_DIR / f"token-{_token_suffix()}"


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_tokens(access: str, refresh: str):
    ensure_config_dir()
    path = _token_path()
    with open(path, "w") as f:
        json.dump({"access": access, "refresh": refresh}, f)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load_tokens() -> dict | None:
    path = _token_path()
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        if "access" in data and "refresh" in data:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def clear_tokens():
    path = _token_path()
    if path.exists():
        path.unlink()
