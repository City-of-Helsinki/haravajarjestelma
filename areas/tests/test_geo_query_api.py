from datetime import date, datetime, timedelta

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.utils.timezone import localtime, make_aware, now
from freezegun import freeze_time
from rest_framework.reverse import reverse

from common.tests.utils import check_translated_field_data_matches_object, get
from events.factories import EventFactory

from ..factories import AddressFactory, ContractZoneFactory

URL = reverse("v1:geo_query-list")

ADDRESS_KEYS = {"street", "distance", "number", "number_end", "letter", "location"}


def get_url(lat, lon):
    return URL + "?lat={}&lon={}".format(lat, lon)


def check_address_data_matches_object(address_data, address_obj):
    assert set(address_data.keys()) == ADDRESS_KEYS

    for field_name in ("number", "number_end", "letter"):
        assert address_data[field_name] == getattr(address_obj, field_name)
    assert len(address_data["location"]["coordinates"]) == 2

    street_data = address_data["street"]
    assert set(street_data.keys()) == {"name"}
    check_translated_field_data_matches_object(street_data, address_obj.street, "name")


@pytest.fixture(autouse=True)
def set_frozen_time():
    freezer = freeze_time("2018-11-01T08:00:00Z")
    freezer.start()
    yield
    freezer.stop()


@pytest.fixture(autouse=True)
def override_settings(settings):
    settings.EVENT_MINIMUM_DAYS_BEFORE_START = 7
    settings.EVENT_MAXIMUM_COUNT_PER_CONTRACT_ZONE = 3


@pytest.fixture
def addresses():
    return [AddressFactory(location=Point((lon, 60))) for lon in (24, 27, 30)]


@pytest.fixture
def contract_zone():
    return ContractZoneFactory(
        boundary=MultiPolygon(
            Polygon(((24, 60), (25, 60), (25, 61), (24, 61), (24, 60)))
        )
    )


def test_required_parameters(api_client):
    response_data = get(api_client, URL)
    assert all(param in response_data for param in ("lat", "lon"))


def test_no_address_objects_in_database(api_client):
    response_data = get(api_client, get_url(60.0, 24.0))
    assert response_data["closest_address"] is None


def test_closest_address_check_data(api_client, addresses):
    response_data = get(api_client, get_url(60.0, 26.0))
    check_address_data_matches_object(response_data["closest_address"], addresses[1])


def test_no_matching_contract_zone(api_client, contract_zone):
    response_data = get(api_client, get_url(67, 24.5))
    assert response_data["contract_zone"] is None


def test_contract_zone_check_data(api_client, contract_zone):
    response_data = get(api_client, get_url(60, 24))
    contract_zone_data = response_data["contract_zone"]
    assert contract_zone_data.keys() == {"id", "name", "active", "unavailable_dates"}
    assert contract_zone_data["id"] == contract_zone.id
    assert contract_zone_data["name"] == contract_zone.name
    assert contract_zone_data["active"] == contract_zone.active
    assert contract_zone_data["unavailable_dates"]


def test_too_early_days_included_in_unavailable_dates(api_client, contract_zone):
    today = localtime(now()).date()

    response_data = get(api_client, get_url(60, 24))
    dates = response_data["contract_zone"]["unavailable_dates"]

    assert dates == [
        today,
        today + timedelta(days=1),
        today + timedelta(days=2),
        today + timedelta(days=3),
        today + timedelta(days=4),
        today + timedelta(days=5),
        today + timedelta(days=6),
        today + timedelta(days=7),
    ]


@pytest.mark.parametrize(
    "event_days, expected_unavailable_days",
    [
        ([10, 10], []),  # normal Monday
        ([9, 9], []),  # Sunday
        ([6, 6], []),  # holiday
        ([5, 6, 6], [5, 6]),  # 6 = holiday
        ([10, 10, 10], [10]),  # max num of events is 3
        ([14, 14, 14], [14, 15, 16]),  # 14 = Friday
        ([14, 15, 16], [14, 15, 16]),
        ([21, 22, 23], [21, 22, 23, 24, 25, 26]),  # 21 = Friday, 24-26 holidays
    ],
)
def test_unavailable_dates(
    api_client, contract_zone, event_days, expected_unavailable_days
):
    """
    Test how event dates in December 2018 yield unavailable dates (too early dates ignored)
    """
    for event_day in event_days:
        d = make_aware(datetime(2018, 12, event_day, 11))
        EventFactory(start_time=d, end_time=d + timedelta(hours=1))

    response_data = get(api_client, get_url(60, 24))
    dates = response_data["contract_zone"]["unavailable_dates"][8:]

    assert dates == [date(2018, 12, d) for d in expected_unavailable_days]
