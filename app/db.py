from __future__ import annotations

import json
import os
from typing import Optional

import asyncpg

from routing import ResortCandidate

# ---------------------------------------------------------------------------
# Connection pool
# ---------------------------------------------------------------------------

_pool: Optional[asyncpg.Pool] = None


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=os.environ["DATABASE_URL"],
        min_size=2,
        max_size=10,
    )


async def close_pool() -> None:
    if _pool:
        await _pool.close()


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------

async def get_user_profile(session_id: str) -> Optional[dict]:
    row = await get_pool().fetchrow(
        "SELECT * FROM user_profiles WHERE session_id = $1",
        session_id,
    )
    return dict(row) if row else None


async def upsert_user_profile(session_id: str, updates: dict) -> None:
    existing = await get_user_profile(session_id)
    if not existing:
        await get_pool().execute(
            """
            INSERT INTO user_profiles (session_id, home_airport, skill_level,
                preferred_terrain, budget_level, passport_countries,
                max_drive_hours, visited_resort_ids, favorite_resort_ids)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            session_id,
            updates.get("home_airport", "SNA"),
            updates.get("skill_level"),
            updates.get("preferred_terrain", []),
            updates.get("budget_level"),
            updates.get("passport_countries", ["US"]),
            updates.get("max_drive_hours", 5.0),
            updates.get("visited_resort_ids", []),
            updates.get("favorite_resort_ids", []),
        )
    else:
        fields = []
        values = []
        i = 2
        for key in ("home_airport", "skill_level", "preferred_terrain",
                    "budget_level", "passport_countries", "max_drive_hours"):
            if key in updates:
                fields.append(f"{key} = ${i}")
                values.append(updates[key])
                i += 1
        if not fields:
            return
        fields.append("updated_at = NOW()")
        sql = f"UPDATE user_profiles SET {', '.join(fields)} WHERE session_id = $1"
        await get_pool().execute(sql, session_id, *values)


# ---------------------------------------------------------------------------
# Resorts + forecasts
# ---------------------------------------------------------------------------

async def get_resorts_with_forecasts() -> list[ResortCandidate]:
    """
    Returns all resorts joined with their most recent forecast for today or
    the nearest upcoming date. Used to build the candidate list for scoring.
    """
    rows = await get_pool().fetch(
        """
        SELECT
            r.id, r.name, r.slug, r.continent, r.country, r.hemisphere,
            r.nearest_airport, r.airport_drive_minutes,
            r.season_start_month, r.season_end_month,
            r.avg_annual_snowfall_cm, r.difficulty_mix,
            r.terrain_tags, r.vibe_tags, r.budget_tier, r.agent_notes,
            f.new_snow_cm, f.cumulative_7d_cm, f.base_depth_cm
        FROM resorts r
        LEFT JOIN LATERAL (
            SELECT new_snow_cm, cumulative_7d_cm, base_depth_cm
            FROM snow_forecasts
            WHERE resort_id = r.id
            ORDER BY ABS(forecast_date - CURRENT_DATE)
            LIMIT 1
        ) f ON true
        ORDER BY r.id
        """
    )
    return [
        ResortCandidate(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            continent=row["continent"],
            country=row["country"],
            hemisphere=row["hemisphere"],
            nearest_airport=row["nearest_airport"],
            airport_drive_minutes=row["airport_drive_minutes"],
            season_start_month=row["season_start_month"],
            season_end_month=row["season_end_month"],
            avg_annual_snowfall_cm=row["avg_annual_snowfall_cm"],
            difficulty_mix=json.loads(row["difficulty_mix"]) if row["difficulty_mix"] else {},
            terrain_tags=list(row["terrain_tags"]),
            vibe_tags=list(row["vibe_tags"]),
            budget_tier=row["budget_tier"] or "mid",
            agent_notes=row["agent_notes"] or "",
            new_snow_cm=row["new_snow_cm"],
            cumulative_7d_cm=row["cumulative_7d_cm"],
            base_depth_cm=row["base_depth_cm"],
        )
        for row in rows
    ]


async def get_resort_by_slug(slug: str) -> Optional[dict]:
    row = await get_pool().fetchrow(
        "SELECT * FROM resorts WHERE slug = $1",
        slug,
    )
    return dict(row) if row else None


async def get_resort_by_id(resort_id: int) -> Optional[dict]:
    row = await get_pool().fetchrow(
        "SELECT * FROM resorts WHERE id = $1",
        resort_id,
    )
    return dict(row) if row else None


async def get_latest_forecast(resort_id: int) -> Optional[dict]:
    row = await get_pool().fetchrow(
        """
        SELECT * FROM snow_forecasts
        WHERE resort_id = $1
        ORDER BY ABS(forecast_date - CURRENT_DATE)
        LIMIT 1
        """,
        resort_id,
    )
    return dict(row) if row else None


async def upsert_forecast(
    resort_id: int,
    forecast_date,
    new_snow_cm: Optional[float],
    cumulative_7d_cm: Optional[float],
    base_depth_cm: Optional[int],
    temperature_c: Optional[float],
    wind_kph: Optional[float],
) -> None:
    await get_pool().execute(
        """
        INSERT INTO snow_forecasts
            (resort_id, forecast_date, new_snow_cm, cumulative_7d_cm,
             base_depth_cm, temperature_c, wind_kph, fetched_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        ON CONFLICT (resort_id, forecast_date) DO UPDATE SET
            new_snow_cm      = EXCLUDED.new_snow_cm,
            cumulative_7d_cm = EXCLUDED.cumulative_7d_cm,
            base_depth_cm    = EXCLUDED.base_depth_cm,
            temperature_c    = EXCLUDED.temperature_c,
            wind_kph         = EXCLUDED.wind_kph,
            fetched_at       = NOW()
        """,
        resort_id, forecast_date, new_snow_cm, cumulative_7d_cm,
        base_depth_cm, temperature_c, wind_kph,
    )


# ---------------------------------------------------------------------------
# Flight routes
# ---------------------------------------------------------------------------

async def get_flight_table(origin: str) -> dict[tuple[str, str], int]:
    """Returns {(origin, destination): flight_minutes} for a given origin."""
    rows = await get_pool().fetch(
        "SELECT origin, destination, flight_minutes FROM flight_routes WHERE origin = $1",
        origin,
    )
    return {(row["origin"], row["destination"]): row["flight_minutes"] for row in rows}


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------

async def save_message(session_id: str, role: str, content: str) -> None:
    await get_pool().execute(
        "INSERT INTO conversations (session_id, role, content) VALUES ($1, $2, $3)",
        session_id, role, content,
    )


async def get_conversation_history(session_id: str, limit: int = 20) -> list[dict]:
    rows = await get_pool().fetch(
        """
        SELECT role, content FROM conversations
        WHERE session_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        session_id, limit,
    )
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
