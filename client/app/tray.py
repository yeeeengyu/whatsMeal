import logging
import threading
from typing import Any, Protocol


class TrayController(Protocol):
    def show_popup(self) -> None:
        ...

    def refresh_today(self) -> None:
        ...

    def quit_app(self) -> None:
        ...


class MealTray:
    def __init__(self, controller: TrayController) -> None:
        import pystray

        self._controller = controller
        self._icon = pystray.Icon(
            "WhatsMeal",
            _create_icon(),
            "경소고 급식",
            menu=pystray.Menu(
                pystray.MenuItem("급식 보기", self._show_popup, default=True),
                pystray.MenuItem("새로고침", self._refresh_today),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("종료", self._quit),
            ),
        )
        self._started = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._started:
            return

        try:
            self._icon.run_detached()
        except NotImplementedError:
            self._thread = threading.Thread(target=self._icon.run, daemon=True)
            self._thread.start()

        self._started = True
        logging.info("Tray icon started")

    def stop(self) -> None:
        self._icon.stop()
        logging.info("Tray icon stopped")

    def _show_popup(self, icon, item) -> None:
        self._controller.show_popup()

    def _refresh_today(self, icon, item) -> None:
        self._controller.refresh_today()

    def _quit(self, icon, item) -> None:
        self._controller.quit_app()


def _create_icon() -> Any:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6, 6, 58, 58), radius=12, fill="#1f6feb")
    draw.rounded_rectangle((18, 17, 46, 22), radius=2, fill="#ffffff")
    draw.rounded_rectangle((18, 29, 46, 34), radius=2, fill="#ffffff")
    draw.rounded_rectangle((18, 41, 38, 46), radius=2, fill="#ffffff")
    return image
