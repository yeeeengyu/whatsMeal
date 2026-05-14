from datetime import date
from typing import Any

import httpx

from app.cache import cache, meal_cache_expires_at
from app.config import Settings
from app.utils import clean_dish_text, now_kst, to_neis_date

BASE_URL = "https://open.neis.go.kr/hub"


class NeisFetchError(Exception):
    pass


class SchoolNotFoundError(Exception):
    pass


class MealNotFoundError(Exception):
    pass


async def _neis_get(endpoint: str, params: dict[str, Any], settings: Settings) -> dict[str, Any]:
    request_params = {
        "KEY": settings.neis_api_key,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        **params,
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.get(f"{BASE_URL}/{endpoint}", params=request_params)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise NeisFetchError from exc

    result = data.get("RESULT")
    if result:
        code = result.get("CODE")
        if code == "INFO-200":
            return data
        raise NeisFetchError

    return data


def _extract_rows(data: dict[str, Any], root_key: str) -> list[dict[str, Any]]:
    sections = data.get(root_key)
    if not isinstance(sections, list) or len(sections) < 2:
        return []

    rows = sections[1].get("row", [])
    if not isinstance(rows, list):
        return []

    return rows


async def get_default_school(settings: Settings) -> dict[str, str]:
    if not settings.default_region_code or not settings.default_school_code:
        raise SchoolNotFoundError

    return {
        "name": settings.school_name,
        "region_code": settings.default_region_code,
        "school_code": settings.default_school_code,
    }


async def get_meals_for_date(meal_date: date, settings: Settings) -> dict[str, Any]:
    school = await get_default_school(settings)
    neis_date = to_neis_date(meal_date)
    cache_key = f"meal:{school['region_code']}:{school['school_code']}:{neis_date}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _neis_get(
        "mealServiceDietInfo",
        {
            "ATPT_OFCDC_SC_CODE": school["region_code"],
            "SD_SCHUL_CODE": school["school_code"],
            "MLSV_YMD": neis_date,
        },
        settings,
    )
    rows = _extract_rows(data, "mealServiceDietInfo")
    if not rows:
        raise MealNotFoundError

    meals_by_type = {"중식": [], "석식": []}
    for row in rows:
        meal_type = row.get("MMEAL_SC_NM")
        if meal_type in meals_by_type:
            meals_by_type[meal_type] = clean_dish_text(row.get("DDISH_NM", ""))

    result = {
        "date": meal_date.isoformat(),
        "school": school,
        "lunch": meals_by_type["중식"],
        "dinner": meals_by_type["석식"],
    }

    if not result["lunch"] and not result["dinner"]:
        raise MealNotFoundError

    cache.set(cache_key, result, meal_cache_expires_at(now_kst()))
    return result
