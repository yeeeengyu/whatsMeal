from dataclasses import dataclass
from typing import Any

import httpx

from app.config import DEFAULT_SCHOOL_NAME, AppConfig


class MealApiError(Exception):
    pass


class MealNotFoundError(MealApiError):
    pass


class SchoolNotFoundError(MealApiError):
    pass


class InvalidDateError(MealApiError):
    pass


@dataclass(frozen=True)
class MealData:
    date: str
    school_name: str
    lunch: list[str]
    dinner: list[str]


class MealApiClient:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def get_today(self, school_name: str | None = None) -> MealData:
        return self._request("/api/meals/today", school_name)

    def get_by_date(self, date_value: str, school_name: str | None = None) -> MealData:
        return self._request(f"/api/meals/date/{date_value}", school_name)

    def _request(self, path: str, school_name: str | None = None) -> MealData:
        url = f"{self._config.api_base_url}{path}"
        params = {"school_name": school_name.strip()} if school_name and school_name.strip() else None

        try:
            response = httpx.get(url, params=params, timeout=self._config.request_timeout)
        except httpx.HTTPError as exc:
            raise MealApiError("백엔드에 연결할 수 없습니다.") from exc

        if response.status_code == 400:
            raise InvalidDateError("날짜 형식이 올바르지 않습니다.")
        if response.status_code == 404:
            if _error_detail(response) == "School not found":
                raise SchoolNotFoundError("학교를 찾을 수 없습니다.")
            raise MealNotFoundError("급식 정보가 없습니다.")
        if response.status_code >= 500:
            raise MealApiError("백엔드에서 급식을 불러오지 못했습니다.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise MealApiError("백엔드 응답을 읽을 수 없습니다.") from exc

        return _parse_meal(payload)


def _parse_meal(payload: dict[str, Any]) -> MealData:
    school = payload.get("school") or {}
    return MealData(
        date=str(payload.get("date", "")),
        school_name=str(school.get("name", DEFAULT_SCHOOL_NAME)),
        lunch=_string_list(payload.get("lunch")),
        dinner=_string_list(payload.get("dinner")),
    )


def _error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return ""

    return str(payload.get("detail", ""))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
