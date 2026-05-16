import os
import sys
import tempfile
import traceback
from pathlib import Path

from app.diagnostics import get_log_path, setup_logging

_INSTANCE_LOCK = None


def run_app() -> int:
    import logging

    global _INSTANCE_LOCK
    _INSTANCE_LOCK = SingleInstanceLock("whatsmeal-client")
    if not _INSTANCE_LOCK.acquire():
        logging.info("WhatsMeal is already running")
        return 0

    from app.api import MealApiClient
    from app.config import load_config
    from app.web_popup import WebMealApp

    logging.info("Starting WhatsMeal from %s", sys.executable)
    logging.info("Frozen executable: %s", getattr(sys, "frozen", False))

    config = load_config()
    api_client = MealApiClient(config)
    app = WebMealApp(api_client)
    return app.run()


def main() -> int:
    setup_logging()

    try:
        return run_app()
    except Exception:
        error_text = traceback.format_exc()

        import logging

        logging.exception("WhatsMeal failed to start")

        _show_startup_error(
            "경소고 급식 실행 오류",
            f"앱을 시작하지 못했습니다.\n\n로그: {get_log_path()}\n\n{error_text[-1200:]}",
        )

        return 1


class SingleInstanceLock:
    def __init__(self, name: str) -> None:
        self._path = Path(tempfile.gettempdir()) / f"{name}.lock"
        self._file = None

    def acquire(self) -> bool:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self._path.open("a+")
        if self._path.stat().st_size == 0:
            self._file.write("0")
            self._file.flush()
        self._file.seek(0)

        if sys.platform.startswith("win"):
            acquired = self._acquire_windows()
        else:
            acquired = self._acquire_unix()

        if acquired:
            self._file.seek(0)
            self._file.truncate()
            self._file.write(str(os.getpid()))
            self._file.flush()
            self._file.seek(0)

        return acquired

    def _acquire_windows(self) -> bool:
        try:
            import msvcrt

            msvcrt.locking(self._file.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            self._file.close()
            self._file = None
            return False

    def _acquire_unix(self) -> bool:
        try:
            import fcntl

            fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            self._file.close()
            self._file = None
            return False

def _show_startup_error(title: str, message: str) -> None:
    if sys.platform.startswith("win"):
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
            return
        except Exception:
            pass

    print(f"{title}\n{message}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
