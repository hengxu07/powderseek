"""
Layer 1 evals for rank_resorts().

Tests the full pipeline: filter → score → sort → top_n.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.routing import rank_resorts
from tests.conftest import make_ctx, make_resort

FLIGHT_TABLE: dict[tuple[str, str], int] = {}


def _make_snow_resort(slug: str, new_snow_cm: float, **kwargs):
    """Helper to create resorts that differ only by snow quality. kwargs override defaults."""
    params = dict(
        slug=slug,
        name=slug.replace("-", " ").title(),
        new_snow_cm=new_snow_cm,
        cumulative_7d_cm=new_snow_cm * 2,
        base_depth_cm=int(new_snow_cm * 5),
        airport_drive_minutes=60,
        season_start_month=1,
        season_end_month=12,
    )
    params.update(kwargs)
    return make_resort(**params)


# ---------------------------------------------------------------------------
# Sorting and top_n
# ---------------------------------------------------------------------------

def test_results_sorted_by_score_descending():
    high  = _make_snow_resort("high-snow", new_snow_cm=40.0)
    mid   = _make_snow_resort("mid-snow", new_snow_cm=20.0)
    low   = _make_snow_resort("low-snow", new_snow_cm=5.0)
    ctx = make_ctx()

    ranked = rank_resorts([low, mid, high], ctx, FLIGHT_TABLE)
    slugs = [r.slug for r, _ in ranked]
    assert slugs == ["high-snow", "mid-snow", "low-snow"]


def test_scores_are_monotonically_decreasing():
    resorts = [_make_snow_resort(f"resort-{i}", new_snow_cm=float(i * 5)) for i in range(5)]
    ctx = make_ctx()
    ranked = rank_resorts(resorts, ctx, FLIGHT_TABLE)
    scores = [s for _, s in ranked]
    assert scores == sorted(scores, reverse=True)


def test_top_n_limits_results():
    resorts = [_make_snow_resort(f"resort-{i}", new_snow_cm=float(i)) for i in range(10)]
    ctx = make_ctx()
    ranked = rank_resorts(resorts, ctx, FLIGHT_TABLE, top_n=3)
    assert len(ranked) == 3


def test_top_n_larger_than_pool_returns_all():
    resorts = [_make_snow_resort(f"resort-{i}", new_snow_cm=float(i)) for i in range(3)]
    ctx = make_ctx()
    ranked = rank_resorts(resorts, ctx, FLIGHT_TABLE, top_n=10)
    assert len(ranked) == 3


def test_default_top_n_is_five():
    resorts = [_make_snow_resort(f"resort-{i}", new_snow_cm=float(i)) for i in range(8)]
    ctx = make_ctx()
    ranked = rank_resorts(resorts, ctx, FLIGHT_TABLE)
    assert len(ranked) == 5


# ---------------------------------------------------------------------------
# Filtering is applied before ranking
# ---------------------------------------------------------------------------

def test_unreachable_resorts_are_excluded_from_results():
    good     = _make_snow_resort("reachable", new_snow_cm=10.0, airport_drive_minutes=60)
    too_far  = _make_snow_resort("too-far", new_snow_cm=40.0, airport_drive_minutes=500)
    ctx = make_ctx(duration_days=2)  # WEEKEND: max_drive=360

    ranked = rank_resorts([good, too_far], ctx, FLIGHT_TABLE)
    slugs = [r.slug for r, _ in ranked]
    assert "reachable" in slugs
    assert "too-far" not in slugs


def test_high_snow_unreachable_loses_to_low_snow_reachable():
    # A resort with amazing snow but unreachable should not appear
    reachable = _make_snow_resort("reachable", new_snow_cm=5.0, airport_drive_minutes=60)
    powder_bomb = _make_snow_resort("powder-bomb", new_snow_cm=40.0, airport_drive_minutes=500)
    ctx = make_ctx(duration_days=2)  # WEEKEND: max_drive=360

    ranked = rank_resorts([powder_bomb, reachable], ctx, FLIGHT_TABLE)
    assert len(ranked) == 1
    assert ranked[0][0].slug == "reachable"


def test_out_of_season_resorts_excluded():
    in_season = _make_snow_resort("open", new_snow_cm=10.0,
                                  season_start_month=1, season_end_month=12)
    closed    = _make_snow_resort("closed", new_snow_cm=40.0,
                                  season_start_month=6, season_end_month=8)
    ctx = make_ctx(start_date=date(2025, 2, 1))

    ranked = rank_resorts([in_season, closed], ctx, FLIGHT_TABLE)
    slugs = [r.slug for r, _ in ranked]
    assert "open" in slugs
    assert "closed" not in slugs


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_resort_list_returns_empty():
    ctx = make_ctx()
    assert rank_resorts([], ctx, FLIGHT_TABLE) == []


def test_all_resorts_unreachable_returns_empty():
    resorts = [_make_snow_resort(f"resort-{i}", new_snow_cm=10.0, airport_drive_minutes=500)
               for i in range(5)]
    ctx = make_ctx(duration_days=1)  # DAY: max_drive=150
    assert rank_resorts(resorts, ctx, FLIGHT_TABLE) == []


def test_ski_only_resort_still_ranked_for_skier():
    # Snowboard-not-allowed flag is metadata for the agent, not filtered by rank_resorts
    ski_only = _make_snow_resort("ski-only", new_snow_cm=30.0, snowboard_allowed=False)
    ctx = make_ctx()
    ranked = rank_resorts([ski_only], ctx, FLIGHT_TABLE)
    assert len(ranked) == 1
    assert ranked[0][0].snowboard_allowed is False


def test_returned_scores_are_non_negative():
    resorts = [_make_snow_resort(f"resort-{i}", new_snow_cm=float(i)) for i in range(5)]
    ctx = make_ctx()
    ranked = rank_resorts(resorts, ctx, FLIGHT_TABLE)
    for _, score in ranked:
        assert score >= 0.0


def test_returned_scores_are_rounded():
    resorts = [_make_snow_resort("r", new_snow_cm=17.3)]
    ctx = make_ctx()
    ranked = rank_resorts(resorts, ctx, FLIGHT_TABLE)
    _, score = ranked[0]
    # score_resort rounds to 4 decimal places
    assert score == round(score, 4)
