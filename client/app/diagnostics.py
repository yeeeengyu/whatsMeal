import logging
import os
from pathlib import Path


def get_log_path() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        log_dir = Path(appdata) / "WhatsMeal"
    else:
        log_dir = Path.home() / ".whatsmeal"

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "client.log"


def setup_logging() -> None:
    logging.basicConfig(
        filename=get_log_path(),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )
