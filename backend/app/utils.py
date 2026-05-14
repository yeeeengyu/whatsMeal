import html
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def today_kst() -> date:
    return datetime.now(KST).date()


def now_kst() -> datetime:
    return datetime.now(KST)


def parse_meal_date(value: str) -> date:
    normalized = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue
    raise ValueError("Invalid date format")


def to_neis_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def clean_dish_text(text: str) -> list[str]:
    unescaped = html.unescape(text or "")
    with_line_breaks = re.sub(r"<br\s*/?>", "\n", unescaped, flags=re.IGNORECASE)

    dishes: list[str] = []
    for line in with_line_breaks.splitlines():
        without_allergy_numbers = re.sub(r"\([^)]*\)", "", line)
        cleaned = re.sub(r"\s+", " ", without_allergy_numbers).strip()
        if cleaned:
            dishes.append(cleaned)

    return dishes
