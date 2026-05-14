import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from app.api import MealApiClient
from app.popup import MealPopup


class MealTray:
    def __init__(self, api_client: MealApiClient) -> None:
        self.popup = MealPopup(api_client)
        self.tray = QSystemTrayIcon(_create_icon())
        self.tray.setToolTip("경소고 급식")
        self.tray.activated.connect(self._on_activated)
        self.tray.setContextMenu(self._create_menu())

    def show(self) -> None:
        self.tray.show()
        logging.info("Tray show requested. visible=%s", self.tray.isVisible())
        self.tray.showMessage(
            "경소고 급식",
            "급식 위젯이 실행되었습니다.",
            QSystemTrayIcon.MessageIcon.Information,
            1800,
        )
        self.popup.show_near_cursor()
        logging.info("Popup show requested. visible=%s", self.popup.isVisible())
        self.popup.show_today()

    def _create_menu(self) -> QMenu:
        menu = QMenu()

        show_action = QAction("급식 보기")
        show_action.triggered.connect(self.popup.toggle_near_cursor)
        menu.addAction(show_action)

        refresh_action = QAction("새로고침")
        refresh_action.triggered.connect(self.popup.show_today)
        menu.addAction(refresh_action)

        menu.addSeparator()

        quit_action = QAction("종료")
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        return menu

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.popup.toggle_near_cursor()

    def _quit(self) -> None:
        self.tray.hide()
        self.popup.close()
        from PySide6.QtWidgets import QApplication

        QApplication.quit()


def _create_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#1f6feb"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(6, 6, 52, 52, 12, 12)

    painter.setBrush(QColor("#ffffff"))
    painter.drawRoundedRect(18, 17, 28, 5, 2, 2)
    painter.drawRoundedRect(18, 29, 28, 5, 2, 2)
    painter.drawRoundedRect(18, 41, 20, 5, 2, 2)
    painter.end()

    return QIcon(pixmap)
