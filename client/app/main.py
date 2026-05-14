import sys
import traceback

from app.diagnostics import get_log_path, setup_logging


def run_app() -> int:
    import logging

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
