from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Trip tiers
# ---------------------------------------------------------------------------

class TripTier(str, Enum):
    DAY        = "day"        # 1 day
    WEEKEND    = "weekend"    # 2–3 days
    SHORT      = "short"      # 4–5 days
    MEDIUM     = "medium"     # 6–7 days
    LONG       = "long"       # 8–14 days
    EXPEDITION = "expedition" # 15+ days


def classify_tier(duration_days: int) -> TripTier:
    if duration_days == 1:
        return TripTier.DAY
    if duration_days <= 3:
        return TripTier.WEEKEND
    if duration_days <= 5:
        return TripTier.SHORT
    if duration_days <= 7:
        return TripTier.MEDIUM
    if duration_days <= 14:
        return TripTier.LONG
    return TripTier.EXPEDITION


# ---------------------------------------------------------------------------
# Tier configuration
# Defines what's reachable and how the agent should frame recommendations.
# ---------------------------------------------------------------------------

AIRPORT_OVERHEAD_MINUTES = 90   # security + boarding + deplaning, each direction

@dataclass
class TierConfig:
    max_drive_minutes: Optional[int]    # None = no drive limit
    max_flight_minutes: Optional[int]   # None = no flight limit (fly anywhere)
    max_travel_ratio: float             # max fraction of trip that can be travel (each way)
    continents: Optional[list[str]]     # None = all continents
    countries: Optional[list[str]]      # None = all countries
    surprise_mode: bool                 # True = agent encouraged to give creative picks


TIER_CONFIG: dict[TripTier, TierConfig] = {
    TripTier.DAY: TierConfig(
        max_drive_minutes=150,          # 2.5hr — must be back same day
        max_flight_minutes=None,        # no flying for a day trip
        max_travel_ratio=0.20,          # 2.4hr round-trip max on a 12hr ski day
        continents=["north_america"],
        countries=["US"],
        surprise_mode=False,
    ),
    TripTier.WEEKEND: TierConfig(
        max_drive_minutes=360,          # 6hr — leave Friday night, return Sunday
        max_flight_minutes=120,         # short hop (RNO, SLC) only if snow is exceptional
        max_travel_ratio=0.25,
        continents=["north_america"],
        countries=["US"],
        surprise_mode=False,
    ),
    TripTier.SHORT: TierConfig(
        max_drive_minutes=480,          # 8hr — Mammoth overnight or Utah road trip
        max_flight_minutes=240,         # SLC, DEN, RNO viable
        max_travel_ratio=0.20,
        continents=["north_america"],
        countries=["US"],
        surprise_mode=False,
    ),
    TripTier.MEDIUM: TierConfig(
        max_drive_minutes=None,
        max_flight_minutes=360,         # YVR (Whistler), YYC (Banff) now viable
        max_travel_ratio=0.18,
        continents=["north_america"],
        countries=["US", "CA"],
        surprise_mode=True,             # Whistler as a stretch pick
    ),
    TripTier.LONG: TierConfig(
        max_drive_minutes=None,
        max_flight_minutes=None,        # Japan, Europe, NZ, Chile — all on the table
        max_travel_ratio=0.15,
        continents=None,
        countries=None,
        surprise_mode=True,
    ),
    TripTier.EXPEDITION: TierConfig(
        max_drive_minutes=None,
        max_flight_minutes=None,
        max_travel_ratio=0.10,          # 15+ days — even a 2-day travel day is fine
        continents=None,
        countries=None,
        surprise_mode=True,
    ),
}


# ---------------------------------------------------------------------------
# Trip context (populated from user profile + current request)
# ---------------------------------------------------------------------------

@dataclass
class TripContext:
    duration_days: int
    start_date: date
    origin_airport: str             # IATA, e.g. "SNA"
    home_lat: float
    home_lon: float
    skill_level: str                # beginner | intermediate | advanced | expert
    preferred_terrain: list[str]    # from user profile terrain_tags
    budget_level: str               # budget | mid | premium | luxury
    passport_countries: list[str]   # ISO alpha-2 list
    visited_resort_slugs: list[str] = field(default_factory=list)

    @property
    def tier(self) -> TripTier:
        return classify_tier(self.duration_days)

    @property
    def config(self) -> TierConfig:
        return TIER_CONFIG[self.tier]

    def can_reach_by_flight(self, flight_minutes: int) -> bool:
        cfg = self.config
        if cfg.max_flight_minutes is None:
            return True
        return flight_minutes <= cfg.max_flight_minutes

    def can_reach_by_drive(self, drive_minutes: int) -> bool:
        cfg = self.config
        if cfg.max_drive_minutes is None:
            return True
        return drive_minutes <= cfg.max_drive_minutes

    def travel_ratio(self, one_way_travel_minutes: int) -> float:
        """Fraction of total trip time consumed by round-trip travel."""
        round_trip_days = (one_way_travel_minutes * 2) / (60 * 24)
        return round_trip_days / self.duration_days

    def is_in_season(self, season_start_month: int, season_end_month: int, hemisphere: str) -> bool:
        """Check if the trip start date falls within the resort's season."""
        m = self.start_date.month
        if hemisphere == "southern":
            # Southern Hemisphere: season is roughly June–September
            return season_start_month <= m <= season_end_month
        else:
            # Northern Hemisphere: season may wrap Dec→Apr (start > end not expected here,
            # seed data uses calendar months so Dec=12, Apr=4 — just do range check)
            if season_start_month <= season_end_month:
                return season_start_month <= m <= season_end_month
            else:
                # wraps year boundary (e.g. Nov=11 → Apr=4)
                return m >= season_start_month or m <= season_end_month


# ---------------------------------------------------------------------------
# Resort candidate (flat struct from DB query result)
# ---------------------------------------------------------------------------

@dataclass
class ResortCandidate:
    id: int
    slug: str
    name: str
    continent: str
    country: str
    hemisphere: str
    nearest_airport: str
    airport_drive_minutes: int
    season_start_month: int
    season_end_month: int
    avg_annual_snowfall_cm: Optional[int]
    difficulty_mix: dict
    terrain_tags: list[str]
    vibe_tags: list[str]
    budget_tier: str
    agent_notes: str

    # forecast fields (joined from snow_forecasts)
    new_snow_cm: Optional[float] = None
    cumulative_7d_cm: Optional[float] = None
    base_depth_cm: Optional[int] = None

    # populated by routing layer
    flight_minutes: Optional[int] = None       # None = drive-only resort
    one_way_travel_minutes: Optional[int] = None


# ---------------------------------------------------------------------------
# Reachability filter
# ---------------------------------------------------------------------------

def filter_reachable(
    resorts: list[ResortCandidate],
    ctx: TripContext,
    flight_table: dict[tuple[str, str], int],   # (origin, destination) → flight_minutes
) -> list[ResortCandidate]:
    """
    For each resort, determine if it's reachable given trip tier constraints.
    Attaches one_way_travel_minutes to each resort that passes.
    Returns only reachable, in-season resorts.
    """
    cfg = ctx.config
    reachable = []

    for r in resorts:
        # Hemisphere / season check
        if not ctx.is_in_season(r.season_start_month, r.season_end_month, r.hemisphere):
            continue

        # Continent / country filter
        if cfg.continents and r.continent not in cfg.continents:
            continue
        if cfg.countries and r.country not in cfg.countries:
            continue

        # Passport check for international resorts
        if r.country != ctx.passport_countries[0] if ctx.passport_countries else "US":
            if r.country not in ctx.passport_countries and r.country != "US":
                # User needs a passport for this country
                if r.country not in ctx.passport_countries:
                    continue

        # Determine travel time
        flight_key = (ctx.origin_airport, r.nearest_airport)
        flight_mins = flight_table.get(flight_key)

        if flight_mins is not None:
            # Flying: flight + overhead (each way) + airport drive to resort
            one_way = flight_mins + AIRPORT_OVERHEAD_MINUTES + r.airport_drive_minutes
            if not ctx.can_reach_by_flight(flight_mins):
                continue
        else:
            # Drive-only resort (no flight route → assume local drive)
            # Use airport_drive_minutes as a proxy for drive from home
            one_way = r.airport_drive_minutes
            if not ctx.can_reach_by_drive(r.airport_drive_minutes):
                continue

        # Travel ratio check
        if ctx.travel_ratio(one_way) > cfg.max_travel_ratio:
            continue

        r.flight_minutes = flight_mins
        r.one_way_travel_minutes = one_way
        reachable.append(r)

    return reachable


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

BUDGET_RANK = {"budget": 0, "mid": 1, "premium": 2, "luxury": 3}

def score_resort(r: ResortCandidate, ctx: TripContext) -> float:
    """
    Returns a float score (higher = better recommendation).
    Broken into four weighted components:
      - snow_score:    quality and recency of snow forecast
      - travel_score:  penalises resorts that eat too much of the trip
      - terrain_score: how well terrain tags match user preferences
      - budget_score:  how well cost tier aligns with user budget
    """
    # 1. Snow quality (0–1)
    new_snow   = min((r.new_snow_cm or 0) / 40, 1.0)       # 40cm new snow = perfect
    accum      = min((r.cumulative_7d_cm or 0) / 100, 1.0)  # 100cm/week = perfect
    base       = min((r.base_depth_cm or 0) / 250, 1.0)     # 250cm base = perfect
    reliability = min((r.avg_annual_snowfall_cm or 0) / 1500, 1.0)
    snow_score = new_snow * 0.40 + accum * 0.30 + base * 0.20 + reliability * 0.10

    # 2. Travel efficiency (0–1) — penalise resorts where travel eats the trip
    ratio = ctx.travel_ratio(r.one_way_travel_minutes or 0)
    travel_score = max(0.0, 1.0 - ratio / ctx.config.max_travel_ratio)

    # 3. Terrain match (0–1)
    if ctx.preferred_terrain:
        matched = len(set(ctx.preferred_terrain) & set(r.terrain_tags))
        terrain_score = min(matched / len(ctx.preferred_terrain), 1.0)
    else:
        terrain_score = 0.5   # neutral if user has no preference

    # 4. Budget alignment (0–1)
    user_rank   = BUDGET_RANK.get(ctx.budget_level, 1)
    resort_rank = BUDGET_RANK.get(r.budget_tier, 1)
    budget_score = max(0.0, 1.0 - abs(user_rank - resort_rank) * 0.3)

    # 5. Novelty bonus — slight boost for resorts not yet visited
    novelty = 0.0 if r.slug in ctx.visited_resort_slugs else 0.05

    # Weighted final score
    score = (
        snow_score   * 0.45 +
        travel_score * 0.25 +
        terrain_score * 0.15 +
        budget_score  * 0.10 +
        novelty
    )

    return round(score, 4)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def rank_resorts(
    resorts: list[ResortCandidate],
    ctx: TripContext,
    flight_table: dict[tuple[str, str], int],
    top_n: int = 5,
) -> list[tuple[ResortCandidate, float]]:
    """
    Filter to reachable resorts, score them, return top_n sorted by score.
    The returned list is passed to the Claude agent as context.
    """
    reachable = filter_reachable(resorts, ctx, flight_table)
    scored = [(r, score_resort(r, ctx)) for r in reachable]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


# ---------------------------------------------------------------------------
# Agent prompt builder
# ---------------------------------------------------------------------------

def build_agent_prompt(
    ranked: list[tuple[ResortCandidate, float]],
    ctx: TripContext,
) -> str:
    """
    Builds the system context block fed to the Claude agent.
    The agent uses this + conversation history to write the recommendation.
    """
    tier = ctx.tier
    cfg  = ctx.config

    lines = [
        f"Trip details: {ctx.duration_days} days starting {ctx.start_date}, "
        f"flying out of {ctx.origin_airport}.",
        f"Skier profile: {ctx.skill_level}, prefers {', '.join(ctx.preferred_terrain) or 'no specific terrain'}, "
        f"budget level: {ctx.budget_level}.",
        f"Trip tier: {tier.value}. Surprise/creative picks {'encouraged' if cfg.surprise_mode else 'not applicable — keep it practical'}.",
        "",
        "Candidate resorts (ranked by score, higher = stronger match):",
    ]

    for i, (r, score) in enumerate(ranked, 1):
        travel_desc = (
            f"{r.flight_minutes}min flight + {r.airport_drive_minutes}min drive"
            if r.flight_minutes
            else f"{r.airport_drive_minutes}min drive"
        )
        snow_desc = (
            f"{r.new_snow_cm}cm new snow, {r.cumulative_7d_cm}cm forecast this week, "
            f"{r.base_depth_cm}cm base"
            if r.new_snow_cm is not None
            else "no forecast data available"
        )
        lines.append(
            f"{i}. {r.name} ({r.country}) — score {score}\n"
            f"   Travel: {travel_desc}\n"
            f"   Snow:   {snow_desc}\n"
            f"   Tags:   terrain={r.terrain_tags}, vibe={r.vibe_tags}, budget={r.budget_tier}\n"
            f"   Notes:  {r.agent_notes}"
        )

    lines += [
        "",
        "Write a conversational recommendation explaining the top pick(s) and why. "
        "Include honest tradeoffs. For surprise/long-trip picks, sell the experience — "
        "mention culture, food, unique terrain, and anything that makes it worth the journey. "
        "If the snow forecast is weak everywhere, say so and explain what to watch for.",
    ]

    return "\n".join(lines)
