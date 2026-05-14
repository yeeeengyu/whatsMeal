from dataclasses import dataclass
from typing import Any

import httpx

from app.config import AppConfig


class MealApiError(Exception):
    pass


class MealNotFoundError(MealApiError):
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

    def get_today(self) -> MealData:
        return self._request("/api/meals/today")

    def get_by_date(self, date_value: str) -> MealData:
        return self._request(f"/api/meals/date/{date_value}")

    def _request(self, path: str) -> MealData:
        url = f"{self._config.api_base_url}{path}"

        try:
            response = httpx.get(url, timeout=self._config.request_timeout)
        except httpx.HTTPError as exc:
            raise MealApiError("백엔드에 연결할 수 없습니다.") from exc

        if response.status_code == 400:
            raise InvalidDateError("날짜 형식이 올바르지 않습니다.")
        if response.status_code == 404:
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
        school_name=str(school.get("name", "경북소프트웨어마이스터고등학교")),
        lunch=_string_list(payload.get("lunch")),
        dinner=_string_list(payload.get("dinner")),
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
