"""
Tests for is_in_season() — verifies the dated open/close window from the
season_status worker takes precedence when fresh, with month-range fallback
when the dates are absent or stale.
"""
from __future__ import annotations

from datetime import date, datetime as dt, timedelta, timezone

from app.routing import SEASON_FRESHNESS_DAYS, is_in_season
from tests.conftest import make_resort


def _fresh(updated_days_ago: int = 1) -> dt:
    return dt.now(timezone.utc) - timedelta(days=updated_days_ago)


# ---------------------------------------------------------------------------
# Dated values take precedence
# ---------------------------------------------------------------------------

def test_fresh_dated_range_overrides_month_fallback():
    # Month fallback says open year-round, but dated range says closed today.
    r = make_resort(
        season_start_month=1, season_end_month=12,  # would be "open" by month
        season_open_date=date(2025, 11, 15),
        season_close_date=date(2026, 4, 12),
        season_status_updated_at=_fresh(),
    )
    assert is_in_season(r, date(2026, 1, 1)) is True   # mid-season
    assert is_in_season(r, date(2026, 5, 29)) is False  # after close


def test_dated_range_open_boundary_inclusive():
    r = make_resort(
        season_start_month=1, season_end_month=12,
        season_open_date=date(2025, 11, 15),
        season_close_date=date(2026, 4, 12),
        season_status_updated_at=_fresh(),
    )
    assert is_in_season(r, date(2025, 11, 15)) is True
    assert is_in_season(r, date(2025, 11, 14)) is False


def test_dated_range_close_boundary_inclusive():
    r = make_resort(
        season_start_month=1, season_end_month=12,
        season_open_date=date(2025, 11, 15),
        season_close_date=date(2026, 4, 12),
        season_status_updated_at=_fresh(),
    )
    assert is_in_season(r, date(2026, 4, 12)) is True
    assert is_in_season(r, date(2026, 4, 13)) is False


# ---------------------------------------------------------------------------
# Stale dated values fall back to month range
# ---------------------------------------------------------------------------

def test_stale_dated_range_falls_back_to_month():
    # Dated values present but updated 90 days ago (> SEASON_FRESHNESS_DAYS).
    # The is_in_season call should ignore them and use the month range.
    r = make_resort(
        season_start_month=11, season_end_month=4,    # Nov–Apr fallback
        season_open_date=date(2025, 11, 15),
        season_close_date=date(2026, 4, 12),
        season_status_updated_at=_fresh(SEASON_FRESHNESS_DAYS + 30),
    )
    # The dated close (Apr 12) would have said closed; the stale fallback to
    # month range Nov–Apr says May is closed too — same answer here, so check
    # a day the two disagree:
    #   dated says: Apr 13 → closed (after close)
    #   month says: Apr 13 → in season (Apr is within Nov–Apr)
    assert is_in_season(r, date(2026, 4, 13)) is True  # month fallback wins


# ---------------------------------------------------------------------------
# Missing pieces fall back to month range
# ---------------------------------------------------------------------------

def test_missing_open_date_falls_back_to_month():
    r = make_resort(
        season_start_month=11, season_end_month=4,
        season_open_date=None,
        season_close_date=date(2026, 4, 12),
        season_status_updated_at=_fresh(),
    )
    # July is out of season under Nov–Apr month range.
    assert is_in_season(r, date(2026, 7, 15)) is False
    # February is in season under Nov–Apr month range.
    assert is_in_season(r, date(2026, 2, 15)) is True


def test_no_dated_values_uses_month_range():
    r = make_resort(
        season_start_month=11, season_end_month=4,
        season_open_date=None, season_close_date=None,
        season_status_updated_at=None,
    )
    assert is_in_season(r, date(2026, 2, 15)) is True
    assert is_in_season(r, date(2026, 5, 29)) is False


# ---------------------------------------------------------------------------
# Naive timestamps don't crash the freshness check
# ---------------------------------------------------------------------------

def test_naive_updated_at_treated_as_utc():
    naive_now = dt.now(timezone.utc).replace(tzinfo=None)
    r = make_resort(
        season_start_month=1, season_end_month=12,
        season_open_date=date(2025, 11, 15),
        season_close_date=date(2026, 4, 12),
        season_status_updated_at=naive_now,
    )
    # Should not raise; should use dated branch since "now naive" is treated as UTC.
    assert is_in_season(r, date(2026, 1, 1)) is True
