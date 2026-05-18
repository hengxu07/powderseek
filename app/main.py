from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import date

from dotenv import load_dotenv
load_dotenv()

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import db
import forecast
from agent import run_agent
from models import ChatRequest, ForecastResponse, ProfileUpdate, ResortDetailResponse, ResortResponse
from routing import TripContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: DB pool + forecast scheduler
# ---------------------------------------------------------------------------

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()

    # Schedule forecast refresh every 6 hours; run first one in background
    # so the server starts accepting requests immediately
    scheduler.add_job(forecast.refresh_all_forecasts, "interval", hours=6)
    scheduler.add_job(forecast.refresh_all_forecasts, "date")  # run once at startup
    scheduler.start()

    yield

    scheduler.shutdown()
    await db.close_pool()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Powderseek API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Main conversational endpoint. Streams the agent's response as SSE.

    If `req.trip` is provided, it overrides whatever trip context is stored
    in the user's profile for this request.
    """
    profile = await db.get_user_profile(req.session_id)

    # Build TripContext if trip dates were provided
    trip_ctx = None
    if req.trip:
        home_lat = float(profile["home_lat"]) if profile and profile.get("home_lat") else 33.6846
        home_lon = float(profile["home_lon"]) if profile and profile.get("home_lon") else -117.8265

        trip_ctx = TripContext(
            duration_days=req.trip.duration_days,
            start_date=req.trip.start_date,
            origin_airport=req.trip.origin_airport or (profile or {}).get("home_airport", "SNA"),
            home_lat=home_lat,
            home_lon=home_lon,
            skill_level=req.trip.skill_level or (profile or {}).get("skill_level", "intermediate"),
            preferred_terrain=list((profile or {}).get("preferred_terrain") or []),
            budget_level=req.trip.budget_level or (profile or {}).get("budget_level", "mid"),
            passport_countries=list((profile or {}).get("passport_countries") or ["US"]),
            visited_resort_slugs=[],
        )

    async def event_stream():
        try:
            async for chunk in run_agent(req.session_id, req.message, trip_ctx):
                payload = json.dumps({"type": "text", "content": chunk})
                yield f"data: {payload}\n\n"
        except Exception as e:
            logger.exception("Agent error for session %s", req.session_id)
            error_payload = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {error_payload}\n\n"
        finally:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/resorts", response_model=list[ResortResponse])
async def list_resorts():
    """Returns all resorts with their latest cached forecast."""
    candidates = await db.get_resorts_with_forecasts()
    return [
        ResortResponse(
            id=r.id,
            name=r.name,
            slug=r.slug,
            country=r.country,
            region=None,
            continent=r.continent,
            budget_tier=r.budget_tier,
            terrain_tags=r.terrain_tags,
            vibe_tags=r.vibe_tags,
            pass_affiliations=[],
            nearest_airport=r.nearest_airport,
            airport_drive_minutes=r.airport_drive_minutes,
            season_start_month=r.season_start_month,
            season_end_month=r.season_end_month,
            avg_annual_snowfall_cm=r.avg_annual_snowfall_cm,
            new_snow_cm=r.new_snow_cm,
            cumulative_7d_cm=r.cumulative_7d_cm,
            base_depth_cm=r.base_depth_cm,
        )
        for r in candidates
    ]


@app.get("/resort/{slug}", response_model=ResortDetailResponse)
async def get_resort(slug: str):
    """Returns full resort detail with 7-day forecast array."""
    resort = await db.get_resort_detail(slug)
    if not resort:
        raise HTTPException(status_code=404, detail="Resort not found")
    return resort


@app.get("/forecast/{resort_id}", response_model=ForecastResponse)
async def get_forecast(resort_id: int):
    """Returns the latest cached forecast for a specific resort."""
    resort = await db.get_resort_by_id(resort_id)
    if not resort:
        raise HTTPException(status_code=404, detail="Resort not found")

    row = await db.get_latest_forecast(resort_id)
    if not row:
        raise HTTPException(status_code=404, detail="No forecast data available yet")

    return ForecastResponse(
        resort_id=resort_id,
        resort_name=resort["name"],
        forecast_date=row["forecast_date"],
        new_snow_cm=row["new_snow_cm"],
        cumulative_7d_cm=row["cumulative_7d_cm"],
        base_depth_cm=row["base_depth_cm"],
        temperature_c=float(row["temperature_c"]) if row["temperature_c"] else None,
        wind_kph=float(row["wind_kph"]) if row["wind_kph"] else None,
        fetched_at=str(row["fetched_at"]),
    )


@app.post("/profile")
async def update_profile(req: ProfileUpdate):
    """Upsert user preferences."""
    updates = req.model_dump(exclude={"session_id"}, exclude_none=True)
    await db.upsert_user_profile(req.session_id, updates)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
