from __future__ import annotations

import logging
from datetime import date, timedelta

import httpx

import db

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_resort_forecast(resort_id: int, lat: float, lon: float) -> None:
    """
    Fetch 7-day snow forecast from Open-Meteo for a single resort and
    upsert into the snow_forecasts table.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "snowfall_sum,snow_depth_max,temperature_2m_max,windspeed_10m_max",
        "timezone": "auto",
        "forecast_days": 7,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    daily = data.get("daily", {})
    dates          = daily.get("time", [])
    snowfall       = daily.get("snowfall_sum", [])
    snow_depth     = daily.get("snow_depth_max", [])
    temperature    = daily.get("temperature_2m_max", [])
    wind           = daily.get("windspeed_10m_max", [])

    if not dates:
        logger.warning("No forecast data returned for resort_id=%s", resort_id)
        return

    # Cumulative 7-day snowfall from each date's perspective
    total_snowfall_cm = sum(s for s in snowfall if s is not None)

    for i, day_str in enumerate(dates):
        forecast_date = date.fromisoformat(day_str)
        new_snow_cm   = snowfall[i] if i < len(snowfall) else None
        base_depth_m  = snow_depth[i] if i < len(snow_depth) else None
        temp_c        = temperature[i] if i < len(temperature) else None
        wind_kph      = wind[i] if i < len(wind) else None

        # Convert snow depth from meters to cm
        base_depth_cm = int(base_depth_m * 100) if base_depth_m is not None else None

        # cumulative_7d_cm: remaining snowfall from this date forward
        remaining = sum(
            s for s in snowfall[i:] if s is not None
        )

        await db.upsert_forecast(
            resort_id=resort_id,
            forecast_date=forecast_date,
            new_snow_cm=new_snow_cm,
            cumulative_7d_cm=round(remaining, 1),
            base_depth_cm=base_depth_cm,
            temperature_c=temp_c,
            wind_kph=wind_kph,
        )


async def refresh_all_forecasts() -> None:
    """
    Refresh forecasts for all resorts. Called every 6 hours by the scheduler.
    """
    rows = await db.get_pool().fetch("SELECT id, lat, lon FROM resorts ORDER BY id")
    logger.info("Refreshing forecasts for %d resorts", len(rows))

    for row in rows:
        try:
            await fetch_resort_forecast(row["id"], float(row["lat"]), float(row["lon"]))
        except Exception as e:
            logger.error("Failed to fetch forecast for resort_id=%s: %s", row["id"], e)

    logger.info("Forecast refresh complete")
