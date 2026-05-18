from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator


class TripInput(BaseModel):
    start_date: date
    end_date: date
    origin_airport: str = "SNA"
    skill_level: Optional[str] = None   # beginner | intermediate | advanced | expert
    budget_level: Optional[str] = None  # budget | mid | premium | luxury

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be on or after start_date")
        return v

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1


class ChatRequest(BaseModel):
    session_id: str
    message: str
    trip: Optional[TripInput] = None   # provided on first message, stored in profile after


class ProfileUpdate(BaseModel):
    session_id: str
    home_airport: Optional[str] = None
    skill_level: Optional[str] = None   # beginner | intermediate | advanced | expert
    preferred_terrain: Optional[list[str]] = None
    budget_level: Optional[str] = None  # budget | mid | premium | luxury
    passport_countries: Optional[list[str]] = None
    max_drive_hours: Optional[float] = None


class ResortResponse(BaseModel):
    id: int
    name: str
    slug: str
    country: str
    region: Optional[str]
    continent: str
    budget_tier: Optional[str]
    terrain_tags: list[str]
    vibe_tags: list[str]
    pass_affiliations: list[str]
    nearest_airport: str
    airport_drive_minutes: int
    season_start_month: int
    season_end_month: int
    avg_annual_snowfall_cm: Optional[int]

    # latest forecast (may be None if not yet cached)
    new_snow_cm: Optional[float] = None
    cumulative_7d_cm: Optional[float] = None
    base_depth_cm: Optional[int] = None
    forecast_date: Optional[date] = None


class ForecastDay(BaseModel):
    forecast_date: date
    new_snow_cm: Optional[float]
    cumulative_7d_cm: Optional[float]
    base_depth_cm: Optional[int]
    temperature_c: Optional[float]
    wind_kph: Optional[float]


class ResortDetailResponse(BaseModel):
    id: int
    name: str
    slug: str
    country: str
    continent: str
    region: Optional[str] = None
    lat: float
    lon: float
    elevation_base_m: int
    elevation_summit_m: int
    vertical_drop_m: int
    nearest_airport: str
    airport_drive_minutes: int
    season_start_month: int
    season_end_month: int
    avg_annual_snowfall_cm: Optional[int] = None
    difficulty_mix: Optional[dict] = None
    terrain_tags: list[str]
    vibe_tags: list[str]
    budget_tier: Optional[str] = None
    agent_notes: Optional[str] = None
    forecast_days: list[ForecastDay]


class ForecastResponse(BaseModel):
    resort_id: int
    resort_name: str
    forecast_date: date
    new_snow_cm: Optional[float]
    cumulative_7d_cm: Optional[float]
    base_depth_cm: Optional[int]
    temperature_c: Optional[float]
    wind_kph: Optional[float]
    fetched_at: str
