"""config.py — Load optional API keys from .env and environment."""

from __future__ import annotations

import os
from pathlib import Path


def _load_env_file():
    """Load .env file from repo root if present."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()


def get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


# Optional integrations — agents degrade gracefully when these are absent
SLACK_WEBHOOK_URL = get("SLACK_WEBHOOK_URL")          # https://hooks.slack.com/...
YOUTUBE_API_KEY   = get("YOUTUBE_API_KEY")             # Google Cloud Console
REDDIT_CLIENT_ID  = get("REDDIT_CLIENT_ID")            # Reddit app (optional)
REDDIT_CLIENT_SECRET = get("REDDIT_CLIENT_SECRET")     # Reddit app (optional)
GOOGLE_CALENDAR_CREDENTIALS = get("GOOGLE_CALENDAR_CREDENTIALS")  # path to credentials.json
OLLAMA_URL        = get("OLLAMA_URL", "http://localhost:11434")
