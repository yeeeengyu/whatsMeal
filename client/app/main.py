import sys
import traceback

from app.diagnostics import get_log_path, setup_logging


def run_app() -> int:
    import logging

    from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

    from app.api import MealApiClient
    from app.config import load_config
    from app.tray import MealTray

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("경소고 급식")
    logging.info("Starting WhatsMeal from %s", sys.executable)
    logging.info("Frozen executable: %s", getattr(sys, "frozen", False))

    if not QSystemTrayIcon.isSystemTrayAvailable():
        logging.error("System tray is not available")
        QMessageBox.critical(None, "경소고 급식", "시스템 트레이를 사용할 수 없습니다.")
        return 1

    logging.info("System tray is available")

    config = load_config()
    api_client = MealApiClient(config)
    tray = MealTray(api_client)
    tray.show()

    return app.exec()


def main() -> int:
    setup_logging()

    try:
        return run_app()
    except Exception:
        error_text = traceback.format_exc()

        import logging

        logging.exception("WhatsMeal failed to start")

        try:
            from PySide6.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "경소고 급식 실행 오류",
                f"앱을 시작하지 못했습니다.\n\n로그: {get_log_path()}\n\n{error_text[-1200:]}",
            )
            app.quit()
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
