from __future__ import annotations

from datetime import date

from app.routing import ResortCandidate, TripContext


def make_resort(**overrides) -> ResortCandidate:
    """Factory for ResortCandidate with sensible defaults."""
    defaults = dict(
        id=1,
        slug="test-mountain",
        name="Test Mountain",
        continent="north_america",
        country="US",
        hemisphere="northern",
        nearest_airport="SLC",
        airport_drive_minutes=45,
        season_start_month=1,   # full-year season — avoids date.today() variance
        season_end_month=12,
        avg_annual_snowfall_cm=800,
        difficulty_mix={"green": 20, "blue": 40, "black": 30, "double_black": 10},
        terrain_tags=["groomers", "trees"],
        vibe_tags=["family"],
        budget_tier="mid",
        agent_notes="Test resort.",
        snowboard_allowed=True,
        new_snow_cm=20.0,
        cumulative_7d_cm=50.0,
        base_depth_cm=150,
        one_way_travel_minutes=45,
    )
    defaults.update(overrides)
    return ResortCandidate(**defaults)


def make_ctx(**overrides) -> TripContext:
    """Factory for TripContext with sensible defaults (SHORT trip, SLC origin)."""
    defaults = dict(
        duration_days=5,
        start_date=date(2025, 2, 1),
        origin_airport="SLC",
        home_lat=40.7,
        home_lon=-111.9,
        skill_level="intermediate",
        preferred_terrain=["groomers", "trees"],
        budget_level="mid",
        passport_countries=["US"],
        visited_resort_slugs=[],
    )
    defaults.update(overrides)
    return TripContext(**defaults)
