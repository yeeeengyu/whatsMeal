from PySide6.QtCore import QDate, QThreadPool, Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
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


class MealPopup(QWidget):
    def __init__(self, api_client: MealApiClient) -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self._api_client = api_client
        self._thread_pool = QThreadPool.globalInstance()
        self._last_meal: MealData | None = None

        self.setObjectName("MealPopup")
        self.setFixedSize(360, 520)
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
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        self.title_label = QLabel("경소고 급식")
        self.title_label.setObjectName("TitleLabel")
        self.date_label = QLabel("오늘")
        self.date_label.setObjectName("DateLabel")

        header_text.addWidget(self.title_label)
        header_text.addWidget(self.date_label)

        self.refresh_button = QToolButton()
        self.refresh_button.setText("새로고침")
        self.refresh_button.setObjectName("GhostButton")
        self.refresh_button.clicked.connect(self.show_today)

        self.close_button = QToolButton()
        self.close_button.setText("닫기")
        self.close_button.setObjectName("GhostButton")
        self.close_button.clicked.connect(self.hide)

        header.addLayout(header_text, 1)
        header.addWidget(self.refresh_button)
        header.addWidget(self.close_button)
        root.addLayout(header)

        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.meal_content = QWidget()
        self.meal_layout = QVBoxLayout(self.meal_content)
        self.meal_layout.setContentsMargins(0, 0, 0, 0)
        self.meal_layout.setSpacing(12)
        self.meal_layout.addStretch(1)
        scroll.setWidget(self.meal_content)
        root.addWidget(scroll, 1)

        actions = QHBoxLayout()
        self.copy_button = QPushButton("복사")
        self.copy_button.clicked.connect(self._copy_current_meal)
        actions.addWidget(self.copy_button)
        root.addLayout(actions)

        date_search = QHBoxLayout()
        date_search.setSpacing(8)
        self.date_input = QDateEdit()
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.search_button = QPushButton("날짜 조회")
        self.search_button.setObjectName("SecondaryButton")
        self.search_button.clicked.connect(self._search_date)

        date_search.addWidget(self.date_input, 1)
        date_search.addWidget(self.search_button)
        root.addLayout(date_search)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#MealPopup {
                background: #f7f8fb;
                border: 1px solid #d7dce5;
                border-radius: 8px;
                color: #172033;
                font-family: "Malgun Gothic", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QLabel#TitleLabel {
                font-size: 18px;
                font-weight: 700;
            }
            QLabel#DateLabel {
                color: #667085;
                font-size: 12px;
            }
            QLabel#StatusLabel {
                color: #3b475c;
                min-height: 20px;
            }
            QToolButton#GhostButton {
                background: transparent;
                border: 1px solid #d7dce5;
                border-radius: 6px;
                padding: 5px 8px;
            }
            QToolButton#GhostButton:hover,
            QPushButton:hover {
                background: #edf2f7;
            }
            QPushButton {
                background: #1f6feb;
                color: white;
                border: 0;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton#SecondaryButton {
                background: #344054;
            }
            QDateEdit {
                background: white;
                border: 1px solid #d0d5dd;
                border-radius: 6px;
                padding: 7px 8px;
            }
            QScrollArea {
                background: transparent;
            }
            QFrame#MealSection {
                background: white;
                border: 1px solid #e4e7ec;
                border-radius: 8px;
            }
            QLabel#SectionTitle {
                color: #101828;
                font-weight: 700;
                font-size: 14px;
            }
            QLabel#DishLabel {
                color: #344054;
                line-height: 140%;
            }
            """
        )

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
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        layout.addWidget(title_label)

        if not dishes:
            empty_label = QLabel("정보 없음")
            empty_label.setObjectName("DishLabel")
            layout.addWidget(empty_label)
        else:
            for dish in dishes:
                dish_label = QLabel(f"- {dish}")
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
