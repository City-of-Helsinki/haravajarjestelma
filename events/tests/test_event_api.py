from datetime import timedelta

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.utils import timezone
from django.utils.timezone import localtime
from freezegun import freeze_time
from rest_framework.reverse import reverse

from areas.factories import ContractZoneFactory
from areas.models import ContractZone
from common.tests.utils import assert_objects_in_results, delete, get, patch, post, put
from events.factories import EventFactory
from events.models import Event
from users.factories import UserFactory

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
def make_event_data():
    def _make_event_data(*, contract_zone: ContractZone, **kwargs):
        return {
            "name": "Testitalkoot",
            "description": "Testitalkoissa haravoidaan ahkerasti.",
            "start_time": timezone.now() + timedelta(days=8, hours=6),
            "end_time": timezone.now() + timedelta(days=8, hours=12),
            "location": {
                "type": "Point",
                "coordinates": contract_zone.boundary[0].centroid.tuple,
            },
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
            **kwargs,
        }

    return _make_event_data


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
        assert event_data[field_name] == getattr(event_obj, field_name), (
            f'Field "{field_name}" does not match'
        )

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
        assert field_value == getattr(event_obj, field_name), (
            f'Field "{field_name}" does not match'
        )
    assert event_obj.location


def get_detail_url(event):
    return reverse("v1:event-detail", kwargs={"pk": event.pk})


def test_anonymous_user_get_list_no_results(event, api_client):
    results = get(api_client, LIST_URL)["results"]
    assert len(results) == 0


def test_anonymous_user_get_detail_404(event, api_client):
    get(api_client, get_detail_url(event), 404)


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


def test_regular_user_post_new_event(user_api_client, contract_zone, make_event_data):
    event_data = make_event_data(contract_zone=contract_zone)

    post(user_api_client, LIST_URL, event_data)

    assert Event.objects.count() == 1
    new_event = Event.objects.latest("id")
    check_event_object(new_event, event_data)


def test_official_put_event(official_api_client, event, make_event_data):
    event_data = make_event_data(contract_zone=event.contract_zone)

    put(official_api_client, get_detail_url(event), event_data)

    assert Event.objects.count() == 1
    updated_event = Event.objects.latest("id")
    check_event_object(updated_event, event_data)


def test_official_patch_event(official_api_client, event):
    event.state = Event.WAITING_FOR_APPROVAL
    event.save(update_fields=("state",))
    old_name = event.name

    patch(official_api_client, get_detail_url(event), {"state": "approved"})

    assert Event.objects.count() == 1
    updated_event = Event.objects.latest("id")
    assert updated_event.name == old_name
    assert updated_event.state == "approved"


def test_regular_user_cannot_modify_or_delete_event(
    user_api_client, event, make_event_data
):
    event_data = make_event_data(contract_zone=event.contract_zone)
    url = get_detail_url(event)

    put(user_api_client, url, event_data, 404)
    patch(user_api_client, url, event_data, 404)
    delete(user_api_client, url, 403)


class TestContractor:
    @pytest.fixture
    def contractor_event(self, contractor_api_client):
        event = EventFactory(name="contractor event", state=Event.WAITING_FOR_APPROVAL)
        event.contract_zone.contractor_users.add(contractor_api_client.user)
        return event

    def test_can_partial_update_own_event_state(
        self, contractor_api_client, contractor_event
    ):
        url = get_detail_url(contractor_event)

        patch(contractor_api_client, url, {"state": Event.APPROVED}, 200)

    def test_cannot_partial_update_other_events_state(self, contractor_api_client):
        other_event = EventFactory(
            name="some other contractor's event", state=Event.WAITING_FOR_APPROVAL
        )
        other_event.contract_zone.contractor_users.add(UserFactory())

        url = get_detail_url(other_event)

        # contractor cannot see the event, so the response code should be 404 (since
        # the payload is otherwise correct)
        patch(contractor_api_client, url, {"state": Event.APPROVED}, 404)

    def test_can_update_own_event(
        self, contractor_api_client, contractor_event, make_event_data
    ):
        event_data = make_event_data(contract_zone=contractor_event.contract_zone)
        url = get_detail_url(contractor_event)

        put(contractor_api_client, url, event_data, 200)

    def test_cannot_delete_own_event(self, contractor_api_client, contractor_event):
        url = get_detail_url(contractor_event)

        delete(contractor_api_client, url, 403)

    def test_cannot_update_other_event(
        self, contractor_api_client, event, make_event_data
    ):
        event_data = make_event_data(contract_zone=event.contract_zone)
        url = get_detail_url(event)

        put(contractor_api_client, url, event_data, 404)

    def test_cannot_delete_other_event(self, contractor_api_client, event):
        url = get_detail_url(event)

        delete(contractor_api_client, url, 403)

    def test_can_list_own_events(self, contractor_api_client, contractor_event):
        results = get(contractor_api_client, LIST_URL)["results"]

        assert len(results) == 1

    def test_can_retrieve_own_events(self, contractor_api_client, contractor_event):
        get(contractor_api_client, get_detail_url(contractor_event), 200)

    def test_cannot_list_other_events(self, contractor_api_client, event):
        results = get(contractor_api_client, LIST_URL)["results"]

        assert len(results) == 0

    def test_cannot_retrieve_other_events(self, contractor_api_client, event):
        get(contractor_api_client, get_detail_url(event), 404)


def test_official_can_modify_and_delete_event(
    official_api_client, event, make_event_data
):
    event_data = make_event_data(contract_zone=event.contract_zone)
    url = get_detail_url(event)

    put(official_api_client, url, event_data)
    patch(official_api_client, url, event_data)
    delete(official_api_client, url)


def test_superuser_can_modify_and_delete_event(
    superuser_api_client, event, make_event_data
):
    event_data = make_event_data(contract_zone=event.contract_zone)
    url = get_detail_url(event)

    put(superuser_api_client, url, event_data)
    patch(superuser_api_client, url, event_data)
    delete(superuser_api_client, url)


def test_event_must_start_before_ending(settings, user_api_client, make_event_data):
    full_days_needed = settings.EVENT_MINIMUM_DAYS_BEFORE_START
    event_data = make_event_data(
        contract_zone=ContractZoneFactory(),
        start_time=timezone.now() + timedelta(days=full_days_needed, hours=6),
        end_time=timezone.now() + timedelta(days=full_days_needed, hours=5),
    )

    response_data = post(user_api_client, LIST_URL, event_data, 400)

    assert "Event must start before ending" in response_data["non_field_errors"][0]


def test_cannot_create_event_if_start_is_before_minimum_full_days_in_future(
    settings, user_api_client, contract_zone, make_event_data
):
    full_days_needed = settings.EVENT_MINIMUM_DAYS_BEFORE_START
    beginning_of_today = localtime(timezone.now()).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    minute_before_minimum_start = beginning_of_today + timedelta(
        days=full_days_needed, hours=23, minutes=59
    )
    # "worst case": event submitted at 00:00, start is the last disallowed minute (at 23:59, full_days_needed later)
    event_data = make_event_data(
        contract_zone=contract_zone,
        start_time=minute_before_minimum_start,
        end_time=minute_before_minimum_start + timedelta(hours=6),
    )

    post(user_api_client, LIST_URL, event_data, 400)


def test_can_create_event_if_start_is_minimum_full_days_in_future(
    settings, user_api_client, contract_zone, make_event_data
):
    full_days_needed = settings.EVENT_MINIMUM_DAYS_BEFORE_START
    beginning_of_today = localtime(timezone.now()).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    midnight_of_minimum_start_day = beginning_of_today + timedelta(
        days=full_days_needed + 1
    )
    # event submitted on 00:00, start is the first allowed minute (at 00:00, full_days_needed+1 later)
    event_data = make_event_data(
        contract_zone=contract_zone,
        start_time=midnight_of_minimum_start_day,
        end_time=midnight_of_minimum_start_day + timedelta(hours=6),
    )

    post(user_api_client, LIST_URL, event_data, 201)


def test_event_filtering_by_contract_zone(official_api_client, event):
    contract_zone = event.contract_zone

    another_contract_zone = ContractZoneFactory(
        boundary=MultiPolygon(
            Polygon(((14, 30), (15, 30), (15, 31), (14, 31), (14, 30)))
        )
    )
    event_in_another_contract_zone = EventFactory(
        location=Point(14.5, 30.5), contract_zone=another_contract_zone
    )
    assert event_in_another_contract_zone.contract_zone == another_contract_zone

    results = get(official_api_client, LIST_URL + f"?contract_zone={contract_zone.id}")[
        "results"
    ]

    assert_objects_in_results([event], results)


def test_event_cannot_be_created_in_approved_state(
    api_client, contract_zone, make_event_data
):
    event_data = make_event_data(contract_zone=contract_zone, state=Event.APPROVED)

    post(api_client, LIST_URL, event_data)

    new_event = Event.objects.latest("id")
    assert new_event.state == Event.WAITING_FOR_APPROVAL


def test_event_cannot_be_created_when_days_are_full(
    official_api_client, contract_zone, make_event_data
):
    event_data = make_event_data(contract_zone=contract_zone)
    events = EventFactory.create_batch(
        3,
        contract_zone=contract_zone,
        start_time=event_data["start_time"],
        end_time=event_data["end_time"],
    )
    assert all(event.contract_zone == contract_zone for event in events)

    response_data = post(official_api_client, LIST_URL, event_data, 400)
    assert "Unavailable dates" in response_data["non_field_errors"][0]


def test_event_can_be_modified_when_days_are_full(
    official_api_client, contract_zone, make_event_data
):
    event_data = make_event_data(contract_zone=contract_zone, name="Modified name")
    events = EventFactory.create_batch(
        3,
        contract_zone=contract_zone,
        start_time=event_data["start_time"],
        end_time=event_data["end_time"],
    )
    assert all(event.contract_zone == contract_zone for event in events)
    event = events[0]

    put(official_api_client, get_detail_url(event), event_data)

    event.refresh_from_db()
    assert event.name == "Modified name"
