import pytest
from datetime import datetime
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.utils.timezone import make_aware
from rest_framework.reverse import reverse

from common.tests.utils import get
from events.factories import EventFactory
from events.models import Event

from ..factories import ContractZoneFactory

LIST_URL = reverse("v1:contractzone-list")


@pytest.fixture
def contract_zone():
    return ContractZoneFactory(
        boundary=MultiPolygon(
            Polygon(((24, 60), (25, 60), (25, 61), (24, 61), (24, 60)))
        ),
        contact_person="John Doe",
        email="john@doe.com",
        phone="555-1234567",
    )


@pytest.fixture
def two_events_2018():
    return EventFactory.create_batch(2)


@pytest.fixture
def two_events_2019():
    return EventFactory.create_batch(2, start_time=make_aware(datetime(2019, 3, 3)))


def get_expected_base_data(contract_zone):
    return {
        "id": contract_zone.id,
        "name": contract_zone.name,
        "active": contract_zone.active,
    }


def get_expected_base_data_with_contact_data(contract_zone):
    return dict(
        get_expected_base_data(contract_zone),
        contact_person=contract_zone.contact_person,
        email=contract_zone.email,
        phone=contract_zone.phone,
    )


def test_get_list_non_official_no_stats_no_contact_info(
    contract_zone, two_events_2018, user_api_client
):
    response_data = get(user_api_client, LIST_URL + "?stats_year=2018")

    assert response_data["results"] == [get_expected_base_data(contract_zone)]


def test_get_list_official_no_filter_no_stats_check_contact_data(
    contract_zone, two_events_2018, official_api_client
):
    response_data = get(official_api_client, LIST_URL)

    assert response_data["results"] == [
        get_expected_base_data_with_contact_data(contract_zone)
    ]


def test_get_list_official_check_stats(
    contract_zone, two_events_2018, two_events_2019, official_api_client
):
    non_approved_event_that_should_be_ignored = EventFactory(
        estimated_attendee_count=100000, state=Event.WAITING_FOR_APPROVAL
    )
    assert non_approved_event_that_should_be_ignored.contract_zone == contract_zone
    assert non_approved_event_that_should_be_ignored.start_time.date().year == 2018

    response_data = get(official_api_client, LIST_URL + "?stats_year=2018")

    event_1, event_2 = two_events_2018
    expected_data = dict(
        get_expected_base_data_with_contact_data(contract_zone),
        event_count=2,
        estimated_attendee_count=event_1.estimated_attendee_count
        + event_2.estimated_attendee_count,
    )
    assert response_data["results"] == [expected_data]


def test_get_list_official_check_contact_data(contract_zone, official_api_client):
    response_data = get(official_api_client, LIST_URL)

    assert len(response_data["results"]) == 1
    contract_zone_data = response_data["results"][0]
    assert contract_zone_data["contact_person"] == contract_zone.contact_person
    assert contract_zone_data["email"] == contract_zone.email
    assert contract_zone_data["phone"] == contract_zone.phone
