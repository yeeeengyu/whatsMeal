from PySide6.QtCore import QDate, QSettings, QThreadPool, Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.api import MealApiClient, MealData
from app.workers import ApiWorker


THEMES = {
    "light": {
        "window": "#f6f7f9",
        "window_border": "#cfd6df",
        "text": "#111827",
        "muted": "#526071",
        "control": "#ffffff",
        "control_hover": "#eef2f6",
        "control_border": "#d5dbe3",
        "card": "#ffffff",
        "card_border": "#e1e6ee",
        "dish": "#253044",
        "primary": "#2563eb",
        "primary_hover": "#1d4ed8",
        "secondary": "#344054",
        "secondary_hover": "#1f2937",
        "disabled_bg": "#d8dee8",
        "disabled_text": "#8b95a5",
        "segment": "#e5eaf1",
        "segment_checked": "#111827",
        "segment_checked_text": "#ffffff",
        "selection_bg": "#dbeafe",
        "selection_text": "#111827",
    },
    "dark": {
        "window": "#111827",
        "window_border": "#263244",
        "text": "#f8fafc",
        "muted": "#a9b4c4",
        "control": "#1f2937",
        "control_hover": "#273449",
        "control_border": "#374151",
        "card": "#182131",
        "card_border": "#303b4f",
        "dish": "#e5e7eb",
        "primary": "#3b82f6",
        "primary_hover": "#60a5fa",
        "secondary": "#475569",
        "secondary_hover": "#64748b",
        "disabled_bg": "#2c3647",
        "disabled_text": "#718096",
        "segment": "#0f172a",
        "segment_checked": "#e5e7eb",
        "segment_checked_text": "#0f172a",
        "selection_bg": "#1e40af",
        "selection_text": "#ffffff",
    },
}


class MealPopup(QWidget):
    def __init__(self, api_client: MealApiClient) -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self._api_client = api_client
        self._thread_pool = QThreadPool.globalInstance()
        self._last_meal: MealData | None = None
        self._settings = QSettings("WhatsMeal", "WhatsMeal")
        self._theme = self._load_theme()

        self.setObjectName("MealPopup")
        self.setFixedSize(360, 500)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._build_ui()
        self._apply_styles()

    def show_today(self) -> None:
        self._set_loading("오늘 급식을 불러오는 중...")
        self._run_worker(self._api_client.get_today)

    def show_for_date(self, date_value: str) -> None:
        self._set_loading("급식을 불러오는 중...")
        self._run_worker(lambda: self._api_client.get_by_date(date_value))

    def show_near_cursor(self) -> None:
        active_screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        geometry = active_screen.availableGeometry()
        margin = 14

        self.move(
            geometry.right() - self.width() - margin,
            geometry.bottom() - self.height() - margin,
        )
        self.show()
        self.raise_()
        self.activateWindow()

    def toggle_near_cursor(self) -> None:
        if self.isVisible():
            self.hide()
            return
        self.show_near_cursor()
        if self._last_meal is None:
            self.show_today()

    def focusOutEvent(self, event) -> None:
        self.hide()
        super().focusOutEvent(event)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        header_text = QVBoxLayout()
        header_text.setSpacing(1)

        self.title_label = QLabel("경소고 급식")
        self.title_label.setObjectName("TitleLabel")
        self.date_label = QLabel("오늘")
        self.date_label.setObjectName("DateLabel")

        header_text.addWidget(self.title_label)
        header_text.addWidget(self.date_label)

        self.refresh_button = QToolButton()
        self.refresh_button.setText("새로고침")
        self.refresh_button.setObjectName("GhostButton")
        self.refresh_button.setFixedSize(74, 32)
        self.refresh_button.clicked.connect(self.show_today)

        self.close_button = QToolButton()
        self.close_button.setText("닫기")
        self.close_button.setObjectName("GhostButton")
        self.close_button.setFixedSize(48, 32)
        self.close_button.clicked.connect(self.hide)

        header.addLayout(header_text, 1)
        header.addWidget(self.refresh_button)
        header.addWidget(self.close_button)
        root.addLayout(header)

        theme_row = QHBoxLayout()
        theme_row.setContentsMargins(0, 0, 0, 0)
        theme_row.setSpacing(8)

        theme_label = QLabel("테마")
        theme_label.setObjectName("ThemeLabel")

        theme_selector = QFrame()
        theme_selector.setObjectName("ThemeSelector")
        theme_layout = QHBoxLayout(theme_selector)
        theme_layout.setContentsMargins(2, 2, 2, 2)
        theme_layout.setSpacing(2)

        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)

        self.light_theme_button = QToolButton()
        self.light_theme_button.setText("화이트")
        self.light_theme_button.setObjectName("ThemeButton")
        self.light_theme_button.setCheckable(True)
        self.light_theme_button.setFixedSize(72, 28)
        self.light_theme_button.clicked.connect(lambda: self._set_theme("light"))

        self.dark_theme_button = QToolButton()
        self.dark_theme_button.setText("다크")
        self.dark_theme_button.setObjectName("ThemeButton")
        self.dark_theme_button.setCheckable(True)
        self.dark_theme_button.setFixedSize(64, 28)
        self.dark_theme_button.clicked.connect(lambda: self._set_theme("dark"))

        self.theme_group.addButton(self.light_theme_button)
        self.theme_group.addButton(self.dark_theme_button)
        theme_layout.addWidget(self.light_theme_button)
        theme_layout.addWidget(self.dark_theme_button)

        theme_row.addWidget(theme_label)
        theme_row.addStretch(1)
        theme_row.addWidget(theme_selector)
        root.addLayout(theme_row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        scroll = QScrollArea()
        scroll.setObjectName("MealScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setObjectName("MealViewport")
        scroll.viewport().setAutoFillBackground(False)

        self.meal_content = QWidget()
        self.meal_content.setObjectName("MealContent")
        self.meal_content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.meal_layout = QVBoxLayout(self.meal_content)
        self.meal_layout.setContentsMargins(0, 0, 0, 0)
        self.meal_layout.setSpacing(10)
        self.meal_layout.addStretch(1)
        scroll.setWidget(self.meal_content)
        root.addWidget(scroll, 1)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        self.copy_button = QPushButton("복사")
        self.copy_button.setObjectName("PrimaryButton")
        self.copy_button.setFixedHeight(38)
        self.copy_button.clicked.connect(self._copy_current_meal)
        actions.addWidget(self.copy_button)
        root.addLayout(actions)

        date_search = QHBoxLayout()
        date_search.setSpacing(8)
        date_search.setContentsMargins(0, 2, 0, 0)
        self.date_input = QDateEdit()
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.date_input.setFixedHeight(34)
        self.date_input.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.search_button = QPushButton("날짜 조회")
        self.search_button.setObjectName("SecondaryButton")
        self.search_button.setFixedSize(92, 34)
        self.search_button.clicked.connect(self._search_date)

        date_search.addWidget(self.date_input, 1)
        date_search.addWidget(self.search_button)
        root.addLayout(date_search)

    def _apply_styles(self) -> None:
        palette = THEMES[self._theme]
        self.setStyleSheet(
            f"""
            QWidget#MealPopup {
                background: {palette["window"]};
                border: 1px solid {palette["window_border"]};
                border-radius: 8px;
                color: {palette["text"]};
                font-family: "Malgun Gothic", "Segoe UI", sans-serif;
                font-size: 12px;
            }
            QLabel#TitleLabel {
                color: {palette["text"]};
                font-size: 17px;
                font-weight: 700;
            }
            QLabel#DateLabel {
                color: {palette["muted"]};
                font-size: 12px;
            }
            QLabel#StatusLabel {
                color: {palette["muted"]};
                min-height: 18px;
            }
            QLabel#ThemeLabel {
                color: {palette["muted"]};
                font-weight: 600;
            }
            QFrame#ThemeSelector {
                background: {palette["segment"]};
                border: 1px solid {palette["control_border"]};
                border-radius: 8px;
            }
            QToolButton#ThemeButton {
                background: transparent;
                color: {palette["muted"]};
                border: 0;
                border-radius: 6px;
                font-weight: 700;
            }
            QToolButton#ThemeButton:hover {
                background: {palette["control_hover"]};
                color: {palette["text"]};
            }
            QToolButton#ThemeButton:checked {
                background: {palette["segment_checked"]};
                color: {palette["segment_checked_text"]};
            }
            QToolButton#GhostButton {
                background: {palette["control"]};
                color: {palette["text"]};
                border: 1px solid {palette["control_border"]};
                border-radius: 6px;
                font-weight: 600;
            }
            QToolButton#GhostButton:hover {
                background: {palette["control_hover"]};
            }
            QPushButton#PrimaryButton {
                background: {palette["primary"]};
                color: white;
                border: 0;
                border-radius: 6px;
                padding: 0 12px;
                font-weight: 600;
            }
            QPushButton#PrimaryButton:hover {
                background: {palette["primary_hover"]};
            }
            QPushButton#PrimaryButton:disabled {
                background: {palette["disabled_bg"]};
                color: {palette["disabled_text"]};
            }
            QPushButton#SecondaryButton {
                background: {palette["secondary"]};
                color: white;
                border: 0;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton#SecondaryButton:hover {
                background: {palette["secondary_hover"]};
            }
            QDateEdit {
                background: {palette["control"]};
                color: {palette["text"]};
                selection-background-color: {palette["selection_bg"]};
                selection-color: {palette["selection_text"]};
                border: 1px solid {palette["control_border"]};
                border-radius: 6px;
                padding: 0 8px;
            }
            QScrollArea#MealScroll,
            QWidget#MealViewport,
            QWidget#MealContent {
                background: {palette["window"]};
                border: 0;
            }
            QFrame#MealSection {
                background: {palette["card"]};
                border: 1px solid {palette["card_border"]};
                border-radius: 8px;
            }
            QLabel#SectionTitle {
                color: {palette["text"]};
                font-weight: 700;
                font-size: 14px;
            }
            QLabel#DishLabel {
                color: {palette["dish"]};
                font-size: 12px;
            }
            """
        )
        self.light_theme_button.setChecked(self._theme == "light")
        self.dark_theme_button.setChecked(self._theme == "dark")

    def _load_theme(self) -> str:
        theme = self._settings.value("theme", "light")
        if theme not in THEMES:
            return "light"
        return str(theme)

    def _set_theme(self, theme: str) -> None:
        if theme not in THEMES:
            return

        self._theme = theme
        self._settings.setValue("theme", theme)
        self._apply_styles()

    def _run_worker(self, job) -> None:
        worker = ApiWorker(job)
        worker.signals.finished.connect(self._set_meal)
        worker.signals.failed.connect(self._set_error)
        self._thread_pool.start(worker)

    def _set_loading(self, message: str) -> None:
        self.status_label.setText(message)
        self.copy_button.setEnabled(False)
        self._clear_meals()

    def _set_meal(self, meal: MealData) -> None:
        self._last_meal = meal
        self.date_label.setText(meal.date)
        self.status_label.setText("")
        self.copy_button.setEnabled(True)
        self._clear_meals()
        self._add_meal_section("점심", meal.lunch)
        self._add_meal_section("저녁", meal.dinner)
        self.meal_layout.addStretch(1)

    def _set_error(self, message: str) -> None:
        self.status_label.setText(message)
        self.copy_button.setEnabled(False)
        self._clear_meals()

    def _clear_meals(self) -> None:
        while self.meal_layout.count():
            item = self.meal_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _add_meal_section(self, title: str, dishes: list[str]) -> None:
        frame = QFrame()
        frame.setObjectName("MealSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        layout.addWidget(title_label)

        if not dishes:
            empty_label = QLabel("정보 없음")
            empty_label.setObjectName("DishLabel")
            layout.addWidget(empty_label)
        else:
            for dish in dishes:
                dish_label = QLabel(f"• {dish}")
                dish_label.setObjectName("DishLabel")
                dish_label.setWordWrap(True)
                layout.addWidget(dish_label)

        self.meal_layout.addWidget(frame)

    def _copy_current_meal(self) -> None:
        if self._last_meal is None:
            return

        lines = [f"{self._last_meal.date} 경소고 급식", "", "[점심]"]
        lines.extend(f"- {dish}" for dish in self._last_meal.lunch)
        lines.extend(["", "[저녁]"])
        lines.extend(f"- {dish}" for dish in self._last_meal.dinner)

        QApplication.clipboard().setText("\n".join(lines))
        self.status_label.setText("복사됨")
        QTimer.singleShot(1600, lambda: self.status_label.setText(""))

    def _search_date(self) -> None:
        date_value = self.date_input.date().toString("yyyy-MM-dd")
        self.show_for_date(date_value)
