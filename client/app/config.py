import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    api_base_url: str
    request_timeout: float


def load_config() -> AppConfig:
    load_dotenv()
    load_dotenv(_runtime_env_path(), override=True)

    return AppConfig(
        api_base_url=os.getenv("API_BASE_URL", "http://13.125.46.133:8000").rstrip("/"),
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "7")),
    )


def _runtime_env_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / ".env"
    return Path.cwd() / ".env"
