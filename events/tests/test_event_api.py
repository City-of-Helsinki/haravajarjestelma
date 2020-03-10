from datetime import datetime, time, timedelta

import pytest
from django.conf import settings
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.utils import timezone
from django.utils.timezone import localtime
from freezegun import freeze_time
from rest_framework.reverse import reverse

from areas.factories import ContractZoneFactory
from common.tests.utils import assert_objects_in_results, delete, get, patch, post, put
from events.factories import EventFactory
from events.models import Event

LIST_URL = reverse("v1:event-list")

EXPECTED_EVENT_KEYS = {
    "id",
    "created_at",
    "modified_at",
    "name",
    "description",
    "start_time",
    "end_time",
    "location",
    "state",
    "organizer_first_name",
    "organizer_last_name",
    "organizer_email",
    "organizer_phone",
    "estimated_attendee_count",
    "targets",
    "maintenance_location",
    "additional_information",
    "large_trash_bag_count",
    "small_trash_bag_count",
    "trash_picker_count",
    "contract_zone",
    "equipment_information",
}


@pytest.fixture
def event_data():
    return {
        "name": "Testitalkoot",
        "description": "Testitalkoissa haravoidaan ahkerasti.",
        "start_time": timezone.now() + timedelta(days=8, hours=6),
        "end_time": timezone.now() + timedelta(days=8, hours=12),
        "location": {"type": "Point", "coordinates": [24.95, 60.20]},
        "organizer_first_name": "Matti",
        "organizer_last_name": "Meikäläinen",
        "organizer_email": "matti.meikalainen@tut.fi",
        "organizer_phone": "555-123456",
        "estimated_attendee_count": 1000,
        "targets": "Kaikki mikä ei liiku",
        "maintenance_location": "Kumputie 7",
        "additional_information": "Ei lisätietoja.",
        "large_trash_bag_count": 1000,
        "small_trash_bag_count": 10000,
        "trash_picker_count": 7,
        "equipment_information": "Ei lisätietoja tarvikkeista.",
    }


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


def check_received_event_data(event_data, event_obj):
    """
    Check that data received from the API matches the given object
    """
    assert set(event_data) == EXPECTED_EVENT_KEYS

    simple_fields = (
        "id",
        "name",
        "description",
        "organizer_first_name",
        "organizer_last_name",
        "organizer_email",
        "organizer_phone",
        "estimated_attendee_count",
        "targets",
        "maintenance_location",
        "additional_information",
        "large_trash_bag_count",
        "small_trash_bag_count",
        "trash_picker_count",
        "equipment_information",
    )
    for field_name in simple_fields:
        assert event_data[field_name] == getattr(
            event_obj, field_name
        ), 'Field "{}" does not match'.format(field_name)

    assert event_data["created_at"]
    assert event_data["modified_at"]
    assert len(event_data["location"]["coordinates"]) == 2
    assert event_data["contract_zone"]


def check_event_object(event_obj, event_data):
    """
    Check that a created/updated event object matches the given data
    """
    for field_name, field_value in event_data.items():
        if field_name == "location":
            continue
        assert field_value == getattr(
            event_obj, field_name
        ), 'Field "{}" does not match'.format(field_name)
    assert event_obj.location


def get_detail_url(event):
    return reverse("v1:event-detail", kwargs={"pk": event.pk})


def test_unauthenticated_user_get_list_no_results(event, api_client):
    results = get(api_client, LIST_URL)["results"]
    assert len(results) == 0


def test_unauthenticated_user_get_detail_404(event, api_client):
    get(api_client, get_detail_url(event), 404)


@pytest.mark.parametrize("is_zones_contractor_user", (True, False))
def test_contractor_get_list_check_only_own_received(
    contractor_api_client, event, is_zones_contractor_user
):
    if is_zones_contractor_user:
        event.contract_zone.contractor_users.add(contractor_api_client.user)

    results = get(contractor_api_client, LIST_URL)["results"]

    assert len(results) == (1 if is_zones_contractor_user else 0)


@pytest.mark.parametrize("is_zones_contractor_user", (True, False))
def test_contractor_get_detail_check_only_own_received(
    contractor_api_client, event, is_zones_contractor_user
):
    if is_zones_contractor_user:
        event.contract_zone.contractor_users.add(contractor_api_client.user)

    get(
        contractor_api_client,
        get_detail_url(event),
        200 if is_zones_contractor_user else 404,
    )


def test_official_get_list_check_data(api_client, official, event):
    api_client.force_authenticate(user=official)

    results = get(api_client, LIST_URL)["results"]

    assert len(results) == 1
    data = results[0]
    check_received_event_data(data, event)


def test_official_get_detail_check_data(api_client, official, event):
    api_client.force_authenticate(user=official)

    data = get(api_client, get_detail_url(event))
    check_received_event_data(data, event)


def test_unauthenticated_user_post_new_event(
    user_api_client, contract_zone, event_data
):
    post(user_api_client, LIST_URL, event_data)

    assert Event.objects.count() == 1
    new_event = Event.objects.latest("id")
    check_event_object(new_event, event_data)


def test_official_put_event(official_api_client, event, event_data):
    put(official_api_client, get_detail_url(event), event_data)

    assert Event.objects.count() == 1
    updated_event = Event.objects.latest("id")
    check_event_object(updated_event, event_data)


def test_official_patch_event(official_api_client, event, event_data):
    event.state = Event.WAITING_FOR_APPROVAL
    event.save(update_fields=("state",))
    old_name = event.name
    assert old_name != event_data["name"]

    patch(official_api_client, get_detail_url(event), {"state": "approved"})

    assert Event.objects.count() == 1
    updated_event = Event.objects.latest("id")
    assert updated_event.name == old_name
    assert updated_event.state == "approved"


def test_unauthenticated_user_cannot_modify_or_delete_event(
    user_api_client, event, event_data
):
    url = get_detail_url(event)

    put(user_api_client, url, event_data, 404)
    patch(user_api_client, url, event_data, 404)
    delete(user_api_client, url, 404)


def test_contractor_cannot_modify_or_delete_other_than_own_event(
    contractor_api_client, event, event_data
):
    url = get_detail_url(event)

    put(contractor_api_client, url, event_data, 404)
    patch(contractor_api_client, url, event_data, 404)
    delete(contractor_api_client, url, 404)


def test_contractor_can_modify_and_delete_own_event(
    contractor_api_client, event, event_data
):
    event.contract_zone.contractor_users.add(contractor_api_client.user)
    url = get_detail_url(event)

    put(contractor_api_client, url, event_data)
    patch(contractor_api_client, url, event_data)
    delete(contractor_api_client, url)


def test_official_can_modify_and_delete_event(official_api_client, event, event_data):
    url = get_detail_url(event)

    put(official_api_client, url, event_data)
    patch(official_api_client, url, event_data)
    delete(official_api_client, url)


def test_event_must_start_before_ending(user_api_client, event_data):
    full_days_needed = settings.EVENT_MINIMUM_DAYS_BEFORE_START
    event_data["start_time"] = timezone.now() + timedelta(
        days=full_days_needed, hours=6
    )
    event_data["end_time"] = timezone.now() + timedelta(days=full_days_needed, hours=5)
    response_data = post(user_api_client, LIST_URL, event_data, 400)
    assert "Event must start before ending" in response_data["non_field_errors"][0]


def test_new_event_start_must_be_sufficiently_many_calendar_days_in_future(
    user_api_client, contract_zone, event_data
):
    full_days_needed = settings.EVENT_MINIMUM_DAYS_BEFORE_START
    now = localtime(timezone.now())
    beginning_of_today = datetime.combine(now.date(), time(tzinfo=now.tzinfo))

    # "worst case": event submitted at 00:00, start is the last disallowed minute (at 23:59, full_days_needed later)
    event_data["start_time"] = beginning_of_today + timedelta(
        days=full_days_needed, hours=23, minutes=59
    )
    event_data["end_time"] = event_data["start_time"] + timedelta(hours=6)
    post(user_api_client, LIST_URL, event_data, 400)

    # event submitted on 00:00, start is the first allowed minute (at 00:00, full_days_needed+1 later)
    event_data["start_time"] = beginning_of_today + timedelta(days=full_days_needed + 1)
    event_data["end_time"] = event_data["start_time"] + timedelta(hours=6)
    post(user_api_client, LIST_URL, event_data, 201)


def test_event_filtering_by_contract_zone(official_api_client, event):
    contract_zone = event.contract_zone

    another_contract_zone = ContractZoneFactory(
        boundary=MultiPolygon(
            Polygon(((14, 30), (15, 30), (15, 31), (14, 31), (14, 30)))
        )
    )
    event_in_another_contract_zone = EventFactory(location=Point(14.5, 30.5))
    assert event_in_another_contract_zone.contract_zone == another_contract_zone

    results = get(
        official_api_client, LIST_URL + "?contract_zone={}".format(contract_zone.id)
    )["results"]

    assert_objects_in_results([event], results)


def test_event_cannot_be_created_in_approved_state(
    api_client, contract_zone, event_data
):
    event_data["state"] = Event.APPROVED

    post(api_client, LIST_URL, event_data)

    new_event = Event.objects.latest("id")
    assert new_event.state == Event.WAITING_FOR_APPROVAL


def test_event_cannot_be_created_when_days_are_full(
    official_api_client, contract_zone, event_data
):
    events = EventFactory.create_batch(
        3, start_time=event_data["start_time"], end_time=event_data["end_time"]
    )
    assert all(event.contract_zone == contract_zone for event in events)

    response_data = post(official_api_client, LIST_URL, event_data, 400)
    assert "Unavailable dates" in response_data["non_field_errors"][0]


def test_event_can_be_modified_when_days_are_full(
    official_api_client, contract_zone, event_data
):
    events = EventFactory.create_batch(
        3, start_time=event_data["start_time"], end_time=event_data["end_time"]
    )
    assert all(event.contract_zone == contract_zone for event in events)
    event = events[0]
    event_data["name"] = "Modified name"

    put(official_api_client, get_detail_url(event), event_data)

    event.refresh_from_db()
    assert event.name == "Modified name"
