"""
Layer 1 evals for score_resort().

All tests are pure Python — no LLM calls, no DB, no network.

Weights: snow=0.45, travel=0.25, terrain=0.15, budget=0.10, novelty=+0.05
Out-of-season penalty: -0.60 (clamped at 0.0)
"""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.routing import score_resort
from tests.conftest import make_ctx, make_resort


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_date(fixed: datetime.date):
    """Return a mock that wraps datetime.date but fixes today() to `fixed`."""
    m = MagicMock(wraps=datetime.date)
    m.today.return_value = fixed
    return m


# ---------------------------------------------------------------------------
# Snow component
# ---------------------------------------------------------------------------

def test_perfect_snow_maximises_component():
    # new=40cm, accum=100cm, base=250cm, reliability=1500cm → each sub-component = 1.0
    resort = make_resort(
        new_snow_cm=40.0,
        cumulative_7d_cm=100.0,
        base_depth_cm=250,
        avg_annual_snowfall_cm=1500,
        one_way_travel_minutes=0,
        terrain_tags=["groomers", "trees"],
    )
    ctx = make_ctx(preferred_terrain=["groomers", "trees"], budget_level="mid")
    score = score_resort(resort, ctx)
    # weights: 0.45+0.25+0.15+0.10 = 0.95; + novelty 0.05 = 1.0 max
    assert score == pytest.approx(1.0, abs=0.001)


def test_zero_snow_zeroes_snow_component():
    resort = make_resort(
        new_snow_cm=0,
        cumulative_7d_cm=0,
        base_depth_cm=0,
        avg_annual_snowfall_cm=0,
        one_way_travel_minutes=0,
        terrain_tags=["groomers", "trees"],
    )
    ctx = make_ctx(preferred_terrain=["groomers", "trees"], budget_level="mid")
    score = score_resort(resort, ctx)
    # snow_score=0 → 0*0.45=0; travel=1.0→0.25; terrain=1.0→0.15; budget=1.0→0.10; novelty=0.05
    assert score == pytest.approx(0.55, abs=0.001)


def test_snow_values_capped_at_maxima():
    # 2× the perfect values — scores must still be capped at 1.0 each
    resort = make_resort(
        new_snow_cm=80.0,    # 2× 40cm cap
        cumulative_7d_cm=200.0,  # 2× 100cm cap
        base_depth_cm=500,   # 2× 250cm cap
        avg_annual_snowfall_cm=3000,  # 2× 1500cm cap
        one_way_travel_minutes=0,
        terrain_tags=["groomers", "trees"],
    )
    ctx = make_ctx(preferred_terrain=["groomers", "trees"])
    score = score_resort(resort, ctx)
    assert score == pytest.approx(1.0, abs=0.001)


def test_none_snow_fields_treated_as_zero():
    resort = make_resort(
        new_snow_cm=None,
        cumulative_7d_cm=None,
        base_depth_cm=None,
        avg_annual_snowfall_cm=None,
        one_way_travel_minutes=0,
        terrain_tags=["groomers", "trees"],
    )
    ctx = make_ctx(preferred_terrain=["groomers", "trees"])
    # Same as zero-snow case
    assert score_resort(resort, ctx) == pytest.approx(0.55, abs=0.001)


# ---------------------------------------------------------------------------
# Travel component
# ---------------------------------------------------------------------------
# Using a DAY trip (1 day, max_travel_ratio=0.20) for clean arithmetic.
# travel_ratio = (one_way * 2) / (60*24) / 1 = one_way / 720
# travel_score = max(0, 1 - ratio / 0.20) = max(0, 1 - one_way / 144)

def test_zero_travel_time_gives_perfect_travel_score():
    resort = make_resort(one_way_travel_minutes=0, new_snow_cm=0, cumulative_7d_cm=0,
                         base_depth_cm=0, avg_annual_snowfall_cm=0,
                         terrain_tags=[], season_start_month=1, season_end_month=12)
    ctx = make_ctx(duration_days=1, preferred_terrain=[], budget_level="mid")
    score = score_resort(resort, ctx)
    # travel_score=1.0 → 0.25; snow=0 → 0; terrain=0.5 (no pref) → 0.075; budget=1.0 → 0.10; novelty=0.05
    assert score == pytest.approx(0.475, abs=0.001)


def test_travel_at_max_ratio_gives_zero_travel_score():
    # For DAY trip: max_travel_ratio=0.20, so one_way=144 → travel_score=0.0
    resort = make_resort(one_way_travel_minutes=144, new_snow_cm=0, cumulative_7d_cm=0,
                         base_depth_cm=0, avg_annual_snowfall_cm=0,
                         terrain_tags=[], season_start_month=1, season_end_month=12)
    ctx = make_ctx(duration_days=1, preferred_terrain=[], budget_level="mid")
    score = score_resort(resort, ctx)
    # travel_score=0 → 0.0; snow=0 → 0; terrain=0.5 → 0.075; budget=1.0 → 0.10; novelty=0.05
    assert score == pytest.approx(0.225, abs=0.001)


def test_travel_score_halved_at_midpoint():
    # one_way=72 → ratio=0.10, travel_score = 1 - 0.10/0.20 = 0.5
    resort = make_resort(one_way_travel_minutes=72, new_snow_cm=0, cumulative_7d_cm=0,
                         base_depth_cm=0, avg_annual_snowfall_cm=0,
                         terrain_tags=[], season_start_month=1, season_end_month=12)
    ctx = make_ctx(duration_days=1, preferred_terrain=[], budget_level="mid")
    score = score_resort(resort, ctx)
    # travel_score=0.5 → 0.125; + 0.075 + 0.10 + 0.05
    assert score == pytest.approx(0.35, abs=0.001)


def test_travel_score_clamped_at_zero_when_ratio_exceeds_max():
    # Even if the resort passed filter_reachable, travel_score never goes negative
    resort = make_resort(one_way_travel_minutes=288, new_snow_cm=0, cumulative_7d_cm=0,
                         base_depth_cm=0, avg_annual_snowfall_cm=0,
                         terrain_tags=[], season_start_month=1, season_end_month=12)
    ctx = make_ctx(duration_days=1, preferred_terrain=[], budget_level="mid")
    score = score_resort(resort, ctx)
    # ratio=0.40 > 0.20 → travel_score=max(0, 1-2)=0
    assert score == pytest.approx(0.225, abs=0.001)


# ---------------------------------------------------------------------------
# Terrain component
# ---------------------------------------------------------------------------

def test_full_terrain_match():
    resort = make_resort(terrain_tags=["groomers", "trees"])
    ctx = make_ctx(preferred_terrain=["groomers", "trees"])
    # terrain_score = 2/2 = 1.0
    score = score_resort(resort, ctx)
    # verify terrain contributes 0.15 (score is higher with terrain=1 vs terrain=0)
    resort_no_match = make_resort(terrain_tags=["backcountry"])
    score_no_match = score_resort(resort_no_match, ctx)
    assert score - score_no_match == pytest.approx(0.15, abs=0.001)


def test_no_terrain_match():
    resort = make_resort(terrain_tags=["backcountry", "steeps"])
    ctx = make_ctx(preferred_terrain=["groomers", "trees"])
    # terrain_score = 0/2 = 0.0 → contributes 0
    score = score_resort(resort, ctx)
    resort_full = make_resort(terrain_tags=["groomers", "trees"])
    score_full = score_resort(resort_full, ctx)
    assert score_full - score == pytest.approx(0.15, abs=0.001)


def test_no_terrain_preference_gives_neutral_score():
    resort = make_resort(terrain_tags=["backcountry"])
    ctx = make_ctx(preferred_terrain=[])
    # terrain_score = 0.5 (neutral)
    score = score_resort(resort, ctx)
    # Confirm by checking the terrain contribution is 0.5 * 0.15 = 0.075
    # Build a known total: snow + travel + 0.075 + budget + novelty
    resort2 = make_resort(terrain_tags=["backcountry"], new_snow_cm=0, cumulative_7d_cm=0,
                          base_depth_cm=0, avg_annual_snowfall_cm=0, one_way_travel_minutes=0)
    ctx2 = make_ctx(preferred_terrain=[], budget_level="mid")
    s = score_resort(resort2, ctx2)
    # 0 + 0.25 + 0.075 + 0.10 + 0.05 = 0.475
    assert s == pytest.approx(0.475, abs=0.001)


def test_partial_terrain_match():
    resort = make_resort(terrain_tags=["groomers", "powder", "steeps"])
    ctx = make_ctx(preferred_terrain=["groomers", "trees", "backcountry"])
    # 1 match ("groomers") out of 3 preferred → terrain_score = 1/3
    resort_no = make_resort(terrain_tags=["powder", "steeps"])  # 0 matches
    resort_full = make_resort(terrain_tags=["groomers", "trees", "backcountry"])  # 3 matches

    s_partial = score_resort(resort, ctx)
    s_none = score_resort(resort_no, ctx)
    s_full = score_resort(resort_full, ctx)

    assert s_partial - s_none == pytest.approx((1/3) * 0.15, abs=0.001)
    assert s_full - s_none == pytest.approx(1.0 * 0.15, abs=0.001)


def test_terrain_score_capped_at_one_when_resort_has_extra_tags():
    # Resort has more matching tags than user preferences — still capped at 1.0
    resort = make_resort(terrain_tags=["groomers", "trees", "steeps", "powder"])
    ctx = make_ctx(preferred_terrain=["groomers", "trees"])
    resort_exact = make_resort(terrain_tags=["groomers", "trees"])
    assert score_resort(resort, ctx) == score_resort(resort_exact, ctx)


# ---------------------------------------------------------------------------
# Budget component
# ---------------------------------------------------------------------------
# budget_score = max(0, 1 - abs(user_rank - resort_rank) * 0.3)

@pytest.mark.parametrize("user_budget,resort_budget,expected_budget_score", [
    ("mid",     "mid",     1.0),   # 0 steps apart
    ("budget",  "mid",     0.7),   # 1 step
    ("budget",  "premium", 0.4),   # 2 steps
    ("budget",  "luxury",  0.1),   # 3 steps
    ("luxury",  "budget",  0.1),   # 3 steps reversed
    ("premium", "budget",  0.4),   # 2 steps reversed
])
def test_budget_score(user_budget, resort_budget, expected_budget_score):
    # Isolate: zero snow, zero travel, no terrain pref, no novelty (visited)
    resort = make_resort(
        budget_tier=resort_budget,
        slug="visited",
        new_snow_cm=0, cumulative_7d_cm=0, base_depth_cm=0, avg_annual_snowfall_cm=0,
        one_way_travel_minutes=0, terrain_tags=[],
    )
    ctx = make_ctx(budget_level=user_budget, preferred_terrain=[], visited_resort_slugs=["visited"])
    score = score_resort(resort, ctx)
    # score = 0 + 0.25 + 0.075 + budget_score*0.10 + 0.0 (no novelty)
    expected_total = 0.25 + 0.075 + expected_budget_score * 0.10
    assert score == pytest.approx(expected_total, abs=0.001)


# ---------------------------------------------------------------------------
# Novelty bonus
# ---------------------------------------------------------------------------

def test_novelty_bonus_for_unvisited_resort():
    resort = make_resort(slug="new-mountain", new_snow_cm=0, cumulative_7d_cm=0,
                         base_depth_cm=0, avg_annual_snowfall_cm=0,
                         one_way_travel_minutes=0, terrain_tags=[])
    ctx_fresh = make_ctx(preferred_terrain=[], visited_resort_slugs=[])
    ctx_visited = make_ctx(preferred_terrain=[], visited_resort_slugs=["new-mountain"])
    diff = score_resort(resort, ctx_fresh) - score_resort(resort, ctx_visited)
    assert diff == pytest.approx(0.05, abs=0.001)


def test_no_novelty_for_already_visited_resort():
    resort = make_resort(slug="old-mountain", new_snow_cm=0, cumulative_7d_cm=0,
                         base_depth_cm=0, avg_annual_snowfall_cm=0,
                         one_way_travel_minutes=0, terrain_tags=[])
    ctx = make_ctx(preferred_terrain=[], visited_resort_slugs=["old-mountain"])
    # novelty = 0 because slug is in visited list
    score = score_resort(resort, ctx)
    # 0 + 0.25 + 0.075 + 0.10 + 0.0
    assert score == pytest.approx(0.425, abs=0.001)


# ---------------------------------------------------------------------------
# Out-of-season penalty
# ---------------------------------------------------------------------------

def test_out_of_season_applies_penalty():
    # Summer-only resort (Jun–Aug) checked on Feb 1 → out of season → -0.60 penalty
    resort = make_resort(
        season_start_month=6, season_end_month=8,
        new_snow_cm=40.0, cumulative_7d_cm=100.0, base_depth_cm=250,
        avg_annual_snowfall_cm=1500, one_way_travel_minutes=0,
        terrain_tags=["groomers", "trees"],
    )
    ctx = make_ctx(preferred_terrain=["groomers", "trees"])

    with patch("app.routing.date", _mock_date(datetime.date(2025, 2, 1))):
        score_in = score_resort(make_resort(  # same resort but full-year season
            season_start_month=1, season_end_month=12,
            new_snow_cm=40.0, cumulative_7d_cm=100.0, base_depth_cm=250,
            avg_annual_snowfall_cm=1500, one_way_travel_minutes=0,
            terrain_tags=["groomers", "trees"],
        ), ctx)
        score_out = score_resort(resort, ctx)

    assert score_in - score_out == pytest.approx(0.60, abs=0.001)


def test_out_of_season_score_is_clamped_at_zero():
    # Worst case: no snow + out of season — must not go negative
    resort = make_resort(
        season_start_month=6, season_end_month=8,
        new_snow_cm=0, cumulative_7d_cm=0, base_depth_cm=0,
        avg_annual_snowfall_cm=0, one_way_travel_minutes=0,
        terrain_tags=[],
    )
    ctx = make_ctx(preferred_terrain=[], visited_resort_slugs=["test-mountain"])
    with patch("app.routing.date", _mock_date(datetime.date(2025, 2, 1))):
        score = score_resort(resort, ctx)
    assert score == 0.0


def test_in_season_resort_has_no_penalty():
    # Season wraps year boundary: Nov(11)–Apr(4), trip is in January → in season
    resort = make_resort(season_start_month=11, season_end_month=4)
    ctx = make_ctx()
    with patch("app.routing.date", _mock_date(datetime.date(2025, 1, 15))):
        score_jan = score_resort(resort, ctx)
    with patch("app.routing.date", _mock_date(datetime.date(2025, 7, 15))):
        score_jul = score_resort(resort, ctx)
    # January: in season (no penalty); July: out of season (-0.60)
    assert score_jan - score_jul == pytest.approx(0.60, abs=0.001)


# ---------------------------------------------------------------------------
# Score bounds
# ---------------------------------------------------------------------------

def test_score_never_goes_negative():
    # Adversarial resort: all zeros, out of season, visited, wrong budget
    resort = make_resort(
        season_start_month=6, season_end_month=8,
        new_snow_cm=0, cumulative_7d_cm=0, base_depth_cm=0,
        avg_annual_snowfall_cm=0, one_way_travel_minutes=0,
        terrain_tags=["backcountry"], budget_tier="luxury", slug="visited",
    )
    ctx = make_ctx(preferred_terrain=["groomers"], budget_level="budget",
                   visited_resort_slugs=["visited"])
    with patch("app.routing.date", _mock_date(datetime.date(2025, 2, 1))):
        score = score_resort(resort, ctx)
    assert score == 0.0


def test_score_max_is_1_0():
    # Perfect inputs: all snow maxed, zero travel, full terrain match, exact budget, unvisited
    # weights 0.45+0.25+0.15+0.10 = 0.95; novelty 0.05; total max = 1.0
    resort = make_resort(
        new_snow_cm=40.0, cumulative_7d_cm=100.0, base_depth_cm=250,
        avg_annual_snowfall_cm=1500, one_way_travel_minutes=0,
        terrain_tags=["groomers", "trees"], budget_tier="mid",
    )
    ctx = make_ctx(preferred_terrain=["groomers", "trees"], budget_level="mid",
                   visited_resort_slugs=[])
    score = score_resort(resort, ctx)
    assert score == pytest.approx(1.0, abs=0.001)
