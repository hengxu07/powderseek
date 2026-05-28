import pytest
from app.routing import classify_tier, TripTier


@pytest.mark.parametrize("days,expected", [
    (1,  TripTier.DAY),
    (2,  TripTier.WEEKEND),
    (3,  TripTier.WEEKEND),
    (4,  TripTier.SHORT),
    (5,  TripTier.SHORT),
    (6,  TripTier.MEDIUM),
    (7,  TripTier.MEDIUM),
    (8,  TripTier.LONG),
    (14, TripTier.LONG),
    (15, TripTier.EXPEDITION),
    (30, TripTier.EXPEDITION),
])
def test_classify_tier(days, expected):
    assert classify_tier(days) == expected


def test_boundary_day_to_weekend():
    assert classify_tier(1) == TripTier.DAY
    assert classify_tier(2) == TripTier.WEEKEND


def test_boundary_weekend_to_short():
    assert classify_tier(3) == TripTier.WEEKEND
    assert classify_tier(4) == TripTier.SHORT


def test_boundary_short_to_medium():
    assert classify_tier(5) == TripTier.SHORT
    assert classify_tier(6) == TripTier.MEDIUM


def test_boundary_medium_to_long():
    assert classify_tier(7) == TripTier.MEDIUM
    assert classify_tier(8) == TripTier.LONG


def test_boundary_long_to_expedition():
    assert classify_tier(14) == TripTier.LONG
    assert classify_tier(15) == TripTier.EXPEDITION
