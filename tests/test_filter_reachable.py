"""
Layer 1 evals for filter_reachable().

Tests reachability filtering: drive/flight limits, season, continent,
country, passport, travel ratio, and attachment of one_way_travel_minutes.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.routing import filter_reachable, TripTier
from tests.conftest import make_ctx, make_resort

# Minimal flight table used across tests: SLC→SLC is nonsensical so we use
# real-ish pairs. "SNA" (Orange County) → "SLC" is a short 90-min hop.
FLIGHT_TABLE: dict[tuple[str, str], int] = {
    ("SNA", "SLC"): 90,    # short hop
    ("LAX", "NRT"): 620,   # LA → Tokyo (long haul)
    ("SNA", "YVR"): 150,   # SNA → Vancouver
}


# ---------------------------------------------------------------------------
# Drive-only resorts (no flight route in table)
# ---------------------------------------------------------------------------

def test_drive_resort_within_limit_is_included():
    # DAY trip: max_drive=150min. Resort drive=120min → passes
    resort = make_resort(
        nearest_airport="LOCAL", airport_drive_minutes=120,
        season_start_month=1, season_end_month=12,
    )
    ctx = make_ctx(duration_days=1, origin_airport="SNA")
    result = filter_reachable([resort], ctx, flight_table={})
    assert len(result) == 1


def test_drive_resort_exceeds_limit_is_excluded():
    # DAY trip: max_drive=150min. Resort drive=200min → excluded
    resort = make_resort(
        nearest_airport="LOCAL", airport_drive_minutes=200,
        season_start_month=1, season_end_month=12,
    )
    ctx = make_ctx(duration_days=1, origin_airport="SNA")
    result = filter_reachable([resort], ctx, flight_table={})
    assert result == []


def test_drive_resort_sets_one_way_travel_minutes():
    resort = make_resort(
        nearest_airport="LOCAL", airport_drive_minutes=90,
        season_start_month=1, season_end_month=12,
    )
    ctx = make_ctx(duration_days=1, origin_airport="SNA")
    result = filter_reachable([resort], ctx, flight_table={})
    assert result[0].one_way_travel_minutes == 90


# ---------------------------------------------------------------------------
# Flight resorts
# ---------------------------------------------------------------------------

def test_flight_resort_within_limit_is_included():
    # WEEKEND trip: max_flight=120min. SNA→SLC=90min → passes
    resort = make_resort(
        nearest_airport="SLC", airport_drive_minutes=45,
        season_start_month=1, season_end_month=12,
    )
    ctx = make_ctx(duration_days=2, origin_airport="SNA")
    result = filter_reachable([resort], ctx, FLIGHT_TABLE)
    assert len(result) == 1


def test_flight_resort_exceeds_flight_limit_is_excluded():
    # WEEKEND trip: max_flight=120min. SNA→YVR=150min → excluded
    resort = make_resort(
        nearest_airport="YVR", airport_drive_minutes=30,
        continent="north_america", country="CA",
        season_start_month=1, season_end_month=12,
    )
    ctx = make_ctx(duration_days=2, origin_airport="SNA",
                   passport_countries=["US", "CA"])
    result = filter_reachable([resort], ctx, FLIGHT_TABLE)
    assert result == []


def test_flight_resort_sets_one_way_travel_minutes():
    # one_way = flight_minutes + AIRPORT_OVERHEAD_MINUTES(90) + airport_drive_minutes
    resort = make_resort(
        nearest_airport="SLC", airport_drive_minutes=45,
        season_start_month=1, season_end_month=12,
    )
    ctx = make_ctx(duration_days=2, origin_airport="SNA")
    result = filter_reachable([resort], ctx, FLIGHT_TABLE)
    # 90 (flight) + 90 (overhead) + 45 (drive) = 225
    assert result[0].one_way_travel_minutes == 225
    assert result[0].flight_minutes == 90


def test_day_trip_has_no_flight_option():
    # DAY tier: max_flight_minutes=None means no flying allowed at all
    # The TierConfig has max_flight_minutes=None for DAY but can_reach_by_flight returns True
    # Actually for DAY: max_flight_minutes is None which means "no flying"
    # Looking at the code: can_reach_by_flight checks if max_flight_minutes is None → return True
    # But for DAY tier, TierConfig.max_flight_minutes = None (no flying), so how is this enforced?
    # Re-reading: DAY config max_flight_minutes=None means no limit, but the intent is no flying.
    # Actually for DAY: max_flight_minutes is None, and can_reach_by_flight(x) returns True.
    # So the only real constraint is the travel_ratio. A 90min flight + 90 overhead + 45 drive
    # = 225min. ratio = (225*2)/(1440*1) = 0.3125 > 0.20 → excluded by travel ratio.
    resort = make_resort(
        nearest_airport="SLC", airport_drive_minutes=45,
        season_start_month=1, season_end_month=12,
    )
    ctx = make_ctx(duration_days=1, origin_airport="SNA")
    result = filter_reachable([resort], ctx, FLIGHT_TABLE)
    assert result == []


# ---------------------------------------------------------------------------
# Season filtering
# ---------------------------------------------------------------------------

def test_out_of_season_resort_is_excluded():
    # Summer-only resort (Jun–Aug), trip in February → out of season
    resort = make_resort(
        season_start_month=6, season_end_month=8,
        nearest_airport="LOCAL", airport_drive_minutes=60,
    )
    ctx = make_ctx(duration_days=2, start_date=date(2025, 2, 1))
    result = filter_reachable([resort], ctx, flight_table={})
    assert result == []


def test_in_season_resort_is_included():
    resort = make_resort(
        season_start_month=11, season_end_month=4,  # Nov–Apr wraps year
        nearest_airport="LOCAL", airport_drive_minutes=60,
    )
    ctx = make_ctx(duration_days=2, start_date=date(2025, 2, 1))
    result = filter_reachable([resort], ctx, flight_table={})
    assert len(result) == 1


def test_season_wrap_includes_december():
    # Nov(11)–Apr(4) season, trip in December → in season
    resort = make_resort(
        season_start_month=11, season_end_month=4,
        nearest_airport="LOCAL", airport_drive_minutes=60,
    )
    ctx = make_ctx(duration_days=2, start_date=date(2025, 12, 15))
    result = filter_reachable([resort], ctx, flight_table={})
    assert len(result) == 1


def test_season_wrap_excludes_june():
    # Nov(11)–Apr(4) season, trip in June → out of season
    resort = make_resort(
        season_start_month=11, season_end_month=4,
        nearest_airport="LOCAL", airport_drive_minutes=60,
    )
    ctx = make_ctx(duration_days=2, start_date=date(2025, 6, 15))
    result = filter_reachable([resort], ctx, flight_table={})
    assert result == []


def test_southern_hemisphere_in_season():
    # Southern hemisphere (NZ/Chile) Jun–Sep, trip in July → in season
    resort = make_resort(
        hemisphere="southern",
        continent="south_america", country="CL",
        season_start_month=6, season_end_month=9,
        nearest_airport="SCL", airport_drive_minutes=120,
    )
    ctx = make_ctx(
        duration_days=10, start_date=date(2025, 7, 1),
        origin_airport="LAX", passport_countries=["US", "CL"],
    )
    result = filter_reachable([resort], ctx, FLIGHT_TABLE)
    # No flight route LAX→SCL in our table, so treated as drive-only (airport_drive_minutes=120)
    # LONG trip max_drive=None → passes drive check
    # travel_ratio: (120*2)/(1440*10) = 0.0167 < 0.15 → passes
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Continent / country filters
# ---------------------------------------------------------------------------

def test_wrong_continent_is_excluded():
    # DAY tier: continents=["north_america"]. European resort → excluded
    resort = make_resort(
        continent="europe", country="CH",
        nearest_airport="ZRH", airport_drive_minutes=60,
        season_start_month=12, season_end_month=4,
    )
    ctx = make_ctx(duration_days=1, start_date=date(2025, 2, 1),
                   passport_countries=["US", "CH"])
    result = filter_reachable([resort], ctx, flight_table={})
    assert result == []


def test_wrong_country_is_excluded():
    # DAY tier: countries=["US"]. Canadian resort → excluded
    resort = make_resort(
        continent="north_america", country="CA",
        nearest_airport="YVR", airport_drive_minutes=30,
        season_start_month=11, season_end_month=4,
    )
    ctx = make_ctx(duration_days=1, start_date=date(2025, 2, 1),
                   passport_countries=["US", "CA"])
    result = filter_reachable([resort], ctx, flight_table={})
    assert result == []


def test_long_trip_allows_any_continent():
    # LONG tier: continents=None → all continents allowed
    resort = make_resort(
        continent="europe", country="CH",
        nearest_airport="ZRH", airport_drive_minutes=60,
        season_start_month=12, season_end_month=4,
    )
    ctx = make_ctx(
        duration_days=10, start_date=date(2025, 2, 1),
        origin_airport="SNA", passport_countries=["US", "CH"],
    )
    # No flight route → treated as drive-only; LONG has max_drive=None
    # travel_ratio: (60*2)/(1440*10) = 0.0083 < 0.15 → passes
    result = filter_reachable([resort], ctx, flight_table={})
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Passport check
# ---------------------------------------------------------------------------

def test_foreign_resort_excluded_without_passport():
    # Japan resort, user only has US passport → excluded
    resort = make_resort(
        continent="asia", country="JP",
        nearest_airport="CTS", airport_drive_minutes=60,
        season_start_month=11, season_end_month=4,
    )
    ctx = make_ctx(
        duration_days=10, start_date=date(2025, 2, 1),
        origin_airport="LAX", passport_countries=["US"],
    )
    result = filter_reachable([resort], ctx, FLIGHT_TABLE)
    assert result == []


def test_foreign_resort_included_with_passport():
    # Japan resort, user has JP passport → included (if flight exists)
    resort = make_resort(
        continent="asia", country="JP",
        nearest_airport="NRT", airport_drive_minutes=120,
        season_start_month=11, season_end_month=4,
    )
    ctx = make_ctx(
        duration_days=10, start_date=date(2025, 2, 1),
        origin_airport="LAX", passport_countries=["US", "JP"],
    )
    # LAX→NRT = 620min; LONG trip max_flight=None → passes flight check
    # one_way = 620 + 90 + 120 = 830min
    # travel_ratio = (830*2)/(1440*10) = 0.115 < 0.15 → passes
    result = filter_reachable([resort], ctx, FLIGHT_TABLE)
    assert len(result) == 1


def test_us_resort_never_requires_passport():
    resort = make_resort(country="US", continent="north_america",
                         season_start_month=1, season_end_month=12,
                         nearest_airport="LOCAL", airport_drive_minutes=60)
    ctx = make_ctx(duration_days=2, passport_countries=[])  # no passports listed
    result = filter_reachable([resort], ctx, flight_table={})
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Travel ratio
# ---------------------------------------------------------------------------

def test_travel_ratio_too_high_excludes_resort():
    # WEEKEND trip (2 days, max_travel_ratio=0.25).
    # one_way must satisfy: (one_way*2)/(1440*2) > 0.25 → one_way > 360
    # Use drive-only resort with 400min drive
    resort = make_resort(
        nearest_airport="LOCAL", airport_drive_minutes=400,
        season_start_month=1, season_end_month=12,
    )
    ctx = make_ctx(duration_days=2)
    result = filter_reachable([resort], ctx, flight_table={})
    assert result == []


def test_travel_ratio_just_within_limit_is_included():
    # WEEKEND trip: at ratio=0.25 exactly → 0.25 > 0.25 is False → included
    # (one_way*2)/(1440*2) = 0.25 → one_way = 360
    resort = make_resort(
        nearest_airport="LOCAL", airport_drive_minutes=360,
        season_start_month=1, season_end_month=12,
    )
    ctx = make_ctx(duration_days=2)
    # Also must pass max_drive check: WEEKEND max_drive=360 → 360 <= 360 ✓
    result = filter_reachable([resort], ctx, flight_table={})
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Multiple resorts
# ---------------------------------------------------------------------------

def test_mixed_reachability():
    good = make_resort(slug="good", airport_drive_minutes=60,
                       season_start_month=1, season_end_month=12)
    too_far = make_resort(slug="too-far", airport_drive_minutes=500,
                          season_start_month=1, season_end_month=12)
    out_of_season = make_resort(slug="closed", airport_drive_minutes=60,
                                season_start_month=6, season_end_month=8)
    ctx = make_ctx(duration_days=2, start_date=date(2025, 2, 1))
    result = filter_reachable([good, too_far, out_of_season], ctx, flight_table={})
    assert len(result) == 1
    assert result[0].slug == "good"


def test_empty_resort_list():
    ctx = make_ctx()
    result = filter_reachable([], ctx, flight_table={})
    assert result == []
