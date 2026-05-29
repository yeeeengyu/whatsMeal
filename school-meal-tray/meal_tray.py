import os
import sys
import json
import tempfile
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except ValueError:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3

from gi.repository import Gtk, GLib, Gdk


def runtime_env_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / ".env"
    return Path(__file__).resolve().parent / ".env"


load_dotenv(runtime_env_path())

DEFAULT_API_BASE_URL = "https://port-0-whatsmeal-mcn12bdr8fab7aae.sel5.cloudtype.app"
API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "7"))
DEFAULT_SCHOOL_NAME = "경북소프트웨어마이스터고등학교"
SCHOOL_NAME = os.getenv("SCHOOL_NAME", DEFAULT_SCHOOL_NAME)

_INSTANCE_LOCK = None


def get_meals_by_date(date_value: datetime.date, school_name: str):
    response = requests.get(
        f"{API_BASE_URL}/api/meals/date/{date_value.isoformat()}",
        params={"school_name": normalize_school_name(school_name)},
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code == 400:
        raise RuntimeError("날짜 형식이 올바르지 않습니다.")
    if response.status_code == 404:
        detail = response_detail(response)
        if detail == "School not found":
            raise RuntimeError("학교를 찾을 수 없습니다.")
        raise RuntimeError("급식 정보가 없습니다.")
    if response.status_code >= 500:
        raise RuntimeError("백엔드에서 급식을 불러오지 못했습니다.")

    response.raise_for_status()
    payload = response.json()
    school = payload.get("school") or {}
    school_name = str(school.get("name") or DEFAULT_SCHOOL_NAME)
    meals = {
        "조식": [],
        "중식": string_list(payload.get("lunch")),
        "석식": string_list(payload.get("dinner")),
    }

    return meals, {"school_name": school_name}


def get_today_meals(school_name: str):
    return get_meals_by_date(datetime.date.today(), school_name)


def response_detail(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return ""

    return str(payload.get("detail", ""))


def string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def format_meals_for_copy(meals: dict, date_value: datetime.date, school_name: str) -> str:
    today_text = date_value.strftime("%Y-%m-%d")

    lines = [f"📅 {today_text} {school_name} 급식"]

    meal_map = [
        ("점심", "중식"),
        ("저녁", "석식"),
    ]

    for display_name, key in meal_map:
        lines.append("")
        lines.append(f"[{display_name}]")

        dishes = meals.get(key, [])

        if not dishes:
            lines.append("- 정보 없음")
        else:
            for dish in dishes:
                lines.append(f"- {dish}")

    return "\n".join(lines)


def settings_path() -> Path:
    config_home = os.getenv("XDG_CONFIG_HOME")
    if config_home:
        return Path(config_home) / "whatsmeal" / "settings.json"
    return Path.home() / ".config" / "whatsmeal" / "settings.json"


def normalize_school_name(value: str | None) -> str:
    normalized = (value or "").strip()
    return normalized or DEFAULT_SCHOOL_NAME


def load_settings() -> dict:
    try:
        return json.loads(settings_path().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def save_settings(update: dict) -> None:
    settings = load_settings()
    settings.update(update)
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


class MealTrayApp:
    def __init__(self):
        self.current_meal_text = "아직 급식을 불러오지 않았습니다."
        self.current_date = datetime.date.today()
        self.current_school_name = normalize_school_name(load_settings().get("school_name") or SCHOOL_NAME)
        self.indicator = AppIndicator3.Indicator.new(
            "school-meal-tray",
            "emblem-favorite",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )

        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.refresh()

        # 30분마다 자동 갱신
        GLib.timeout_add_seconds(1800, self.refresh)

    def add_disabled_item(self, menu, text):
        item = Gtk.MenuItem(label=text)
        item.set_sensitive(False)
        menu.append(item)

    def add_meal_section(self, menu, title, dishes):
        self.add_disabled_item(menu, f"🍱 {title}")

        if not dishes:
            self.add_disabled_item(menu, "  정보 없음")
        else:
            for dish in dishes:
                self.add_disabled_item(menu, f"  {dish}")

        menu.append(Gtk.SeparatorMenuItem())

    def refresh(self, *_):
        return self.load_date(self.current_date)

    def load_today(self, *_):
        return self.load_date(datetime.date.today())

    def load_date(self, date_value: datetime.date):
        self.current_date = date_value
        menu = Gtk.Menu()

        date_text = self.current_date.strftime("%Y-%m-%d")
        self.add_disabled_item(menu, f"📅 {date_text}")
        try:
            meals, school = get_meals_by_date(self.current_date, self.current_school_name)
            self.current_school_name = school["school_name"]
            save_settings({"school_name": self.current_school_name})

            self.add_disabled_item(menu, f"🏫 {self.current_school_name}")
            menu.append(Gtk.SeparatorMenuItem())
            self.current_meal_text = format_meals_for_copy(
                meals,
                self.current_date,
                self.current_school_name,
            )

            self.add_meal_section(menu, "점심", meals.get("중식", []))
            self.add_meal_section(menu, "저녁", meals.get("석식", []))

        except Exception as e:
            self.add_disabled_item(menu, f"🏫 {self.current_school_name}")
            menu.append(Gtk.SeparatorMenuItem())
            self.add_disabled_item(menu, "급식 불러오기 실패")
            self.add_disabled_item(menu, str(e)[:80])
            menu.append(Gtk.SeparatorMenuItem())

        copy_item = Gtk.MenuItem(label="급식 복사")
        copy_item.connect("activate", self.copy_meals)
        menu.append(copy_item)

        today_item = Gtk.MenuItem(label="오늘 급식")
        today_item.connect("activate", self.load_today)
        menu.append(today_item)

        date_item = Gtk.MenuItem(label="날짜 조회")
        date_item.connect("activate", self.show_date_dialog)
        menu.append(date_item)

        school_item = Gtk.MenuItem(label="학교 변경")
        school_item.connect("activate", self.show_school_dialog)
        menu.append(school_item)

        refresh_item = Gtk.MenuItem(label="새로고침")
        refresh_item.connect("activate", self.refresh)
        menu.append(refresh_item)

        quit_item = Gtk.MenuItem(label="종료")
        quit_item.connect("activate", Gtk.main_quit)
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)

        return True

    def show_date_dialog(self, *_):
        dialog = Gtk.Dialog(title="날짜 조회")
        dialog.add_button("취소", Gtk.ResponseType.CANCEL)
        dialog.add_button("조회", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_modal(True)
        dialog.set_resizable(False)

        content = dialog.get_content_area()
        content.set_border_width(12)

        label = Gtk.Label(label="조회할 날짜를 입력하세요. 예: 2026-05-15")
        label.set_xalign(0)
        content.pack_start(label, False, False, 0)

        entry = Gtk.Entry()
        entry.set_text(self.current_date.strftime("%Y-%m-%d"))
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 8)

        error_label = Gtk.Label()
        error_label.set_xalign(0)
        content.pack_start(error_label, False, False, 0)

        dialog.show_all()

        while True:
            response = dialog.run()
            if response != Gtk.ResponseType.OK:
                dialog.destroy()
                return

            try:
                date_value = parse_date(entry.get_text())
            except ValueError:
                error_label.set_text("날짜 형식이 올바르지 않습니다.")
                continue

            dialog.destroy()
            self.load_date(date_value)
            return

    def show_school_dialog(self, *_):
        dialog = Gtk.Dialog(title="학교 변경")
        dialog.add_button("취소", Gtk.ResponseType.CANCEL)
        dialog.add_button("적용", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_modal(True)
        dialog.set_resizable(False)

        content = dialog.get_content_area()
        content.set_border_width(12)

        label = Gtk.Label(label="학교 이름을 입력하세요.")
        label.set_xalign(0)
        content.pack_start(label, False, False, 0)

        entry = Gtk.Entry()
        entry.set_text(self.current_school_name)
        entry.set_activates_default(True)
        content.pack_start(entry, False, False, 8)

        dialog.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.current_school_name = normalize_school_name(entry.get_text())
            dialog.destroy()
            self.load_today()
            return

        dialog.destroy()
    
    def copy_meals(self, *_):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(self.current_meal_text, -1)
        clipboard.store()

    def run(self):
        Gtk.main()


def parse_date(value: str) -> datetime.date:
    return datetime.datetime.strptime(value.strip(), "%Y-%m-%d").date()


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


if __name__ == "__main__":
    _INSTANCE_LOCK = SingleInstanceLock("school-meal-tray")
    if not _INSTANCE_LOCK.acquire():
        raise SystemExit(0)

    app = MealTrayApp()
    app.run()
