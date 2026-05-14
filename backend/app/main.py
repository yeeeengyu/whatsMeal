from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.neis import (
    MealNotFoundError,
    NeisFetchError,
    SchoolNotFoundError,
    get_meals_for_date,
)
from app.utils import parse_meal_date, today_kst

app = FastAPI(title="School Meal API", version="0.1.0")

app_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/meals/today")
async def meals_today() -> dict:
    try:
        return await get_meals_for_date(today_kst(), app_settings)
    except SchoolNotFoundError as exc:
        raise HTTPException(status_code=404, detail="School not found") from exc
    except MealNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meal not found") from exc
    except NeisFetchError as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch data from NEIS") from exc


@app.get("/api/meals/date/{date}")
async def meals_by_date(date: str) -> dict:
    try:
        meal_date = parse_meal_date(date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format") from exc

    try:
        return await get_meals_for_date(meal_date, app_settings)
    except SchoolNotFoundError as exc:
        raise HTTPException(status_code=404, detail="School not found") from exc
    except MealNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meal not found") from exc
    except NeisFetchError as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch data from NEIS") from exc

