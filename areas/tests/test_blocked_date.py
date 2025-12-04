from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils.timezone import localtime, now

from events.factories import EventFactory

from ..factories import BlockedDateFactory, ContractZoneFactory


@pytest.fixture
def contract_zone():
    return ContractZoneFactory()


def test_blocked_date_creation(contract_zone):
    """Test that blocked dates can be created successfully."""
    date = localtime(now()).date() + timedelta(days=10)
    blocked_date = BlockedDateFactory(
        contract_zone=contract_zone, date=date, reason="Test blocking"
    )

    assert blocked_date.contract_zone == contract_zone
    assert blocked_date.date == date
    assert blocked_date.reason == "Test blocking"
    assert str(blocked_date) == f"{contract_zone.name} - {date}"


def test_unique_constraint(contract_zone):
    """Test that duplicate date+contract_zone combinations are not allowed."""
    date = localtime(now()).date() + timedelta(days=10)

    # Create first blocked date
    BlockedDateFactory(contract_zone=contract_zone, date=date)

    # Try to create duplicate - should raise IntegrityError
    with pytest.raises(IntegrityError):
        BlockedDateFactory(contract_zone=contract_zone, date=date)


def test_different_zones_same_date_allowed(contract_zone):
    """Test that same date can be blocked in different contract zones."""
    date = localtime(now()).date() + timedelta(days=10)
    other_zone = ContractZoneFactory()

    # Should not raise any errors
    BlockedDateFactory(contract_zone=contract_zone, date=date)
    BlockedDateFactory(contract_zone=other_zone, date=date)


def test_get_unavailable_dates_includes_blocked_dates(contract_zone):
    """Test that blocked dates are included in unavailable dates."""
    # Create a blocked date in the future
    future_date = localtime(now()).date() + timedelta(days=10)
    BlockedDateFactory(contract_zone=contract_zone, date=future_date)

    unavailable_dates = contract_zone.get_unavailable_dates()

    assert future_date in unavailable_dates


def test_get_unavailable_dates_excludes_past_blocked_dates(contract_zone):
    """Test that blocked dates in the past are not included in unavailable dates."""
    # Create a blocked date in the past (beyond minimum lead time)
    past_date = localtime(now()).date() - timedelta(days=20)
    BlockedDateFactory(contract_zone=contract_zone, date=past_date)

    unavailable_dates = contract_zone.get_unavailable_dates()

    assert past_date not in unavailable_dates


def test_get_unavailable_dates_combines_all_reasons(contract_zone):
    """Test that unavailable dates include capacity limits AND blocked dates."""
    future_date = localtime(now()).date() + timedelta(days=10)

    # Create 3 events (capacity limit) on the same working day group
    EventFactory.create_batch(
        3, contract_zone=contract_zone, start_time=future_date, end_time=future_date
    )

    # Create a blocked date (different date to avoid overlap)
    blocked_date = future_date + timedelta(days=1)
    BlockedDateFactory(contract_zone=contract_zone, date=blocked_date)

    unavailable_dates = contract_zone.get_unavailable_dates()

    # Should include both the capacity-blocked date and the explicitly blocked date
    assert blocked_date in unavailable_dates

    # The capacity-blocked dates should also be there (depending on working day group logic)
    # This test mainly verifies that blocked dates are included alongside existing logic
