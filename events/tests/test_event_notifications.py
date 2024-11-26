import pytest
from datetime import timedelta
from django.core import mail
from django.core.management import call_command
from django.utils.timezone import localtime, now
from django_ilmoitin.models import NotificationTemplate
from freezegun import freeze_time

from areas.factories import ContractZoneFactory
from common.utils import assert_to_addresses
from events.factories import EventFactory
from events.models import Event
from events.notifications import NotificationType


@pytest.fixture
def notification_template_event_created():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_CREATED.value,
        subject="test event created subject, event: {{ event.name }}!",
        body_html="<b>test event created body HTML!</b>",
        body_text="test event created body text!",
    )


@pytest.fixture
def notification_template_event_approved_to_organizer():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_APPROVED_TO_ORGANIZER.value,
        subject="hello organizer! event {{ event.name }} approved!",
        body_html="<b>test event approved body HTML!</b>",
        body_text="test event approved body text!",
    )


@pytest.fixture
def notification_template_event_approved_to_contractor():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_APPROVED_TO_CONTRACTOR.value,
        subject="hello contractor! event {{ event.name }} approved!",
        body_html="<b>test event approved body HTML!</b>",
        body_text="test event approved body text!",
    )


@pytest.fixture
def notification_template_event_approved_to_official():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_APPROVED_TO_OFFICIAL.value,
        subject="hello official! event {{ event.name }} approved!",
        body_html="<b>test event approved body HTML!</b>",
        body_text="test event approved body text!",
    )


@pytest.fixture
def notification_template_event_reminder():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_REMINDER.value,
        subject="hello! don't forget event {{ event.name }}!",
        body_html="<b>test event reminder body HTML!</b>",
        body_text="test event reminder body text!",
    )


def test_event_created_notification_is_sent_to_contractors_and_admin(
    notification_template_event_created, official
):
    contract_zone = ContractZoneFactory(
        email="primary@test.test", secondary_email="secondary@test.test"
    )
    event = EventFactory(contract_zone=contract_zone)

    assert len(mail.outbox) == 3
    subject_str = "test event created subject, event: {}!".format(event.name)
    assert mail.outbox[0].subject == subject_str
    assert mail.outbox[1].subject == subject_str
    assert mail.outbox[2].subject == subject_str
    assert_to_addresses(
        official.email, contract_zone.email, contract_zone.secondary_email
    )


def test_notification_is_not_sent_when_event_modified_or_deleted(
    contract_zone, user, notification_template_event_created
):
    event = EventFactory()
    mail.outbox = []

    event.name = "foobar"
    event.save(update_fields=("name",))
    assert len(mail.outbox) == 0

    event.delete()
    assert len(mail.outbox) == 0


def test_event_approved_to_organizer_notification_is_sent_to_organizer_and_contractors_and_official(
    contract_zone,
    user,
    notification_template_event_approved_to_organizer,
    notification_template_event_approved_to_contractor,
    notification_template_event_approved_to_official,
    official,
):
    contract_zone.secondary_email = "mark@example.com"
    contract_zone.save()
    event = EventFactory(
        state=Event.WAITING_FOR_APPROVAL,
        organizer_email="organizer@example.com",
        contract_zone=contract_zone,
    )
    mail.outbox = []
    event.state = Event.APPROVED
    event.save()

    assert len(mail.outbox) == 4
    subject_str = "hello {}! event {} approved!"

    assert mail.outbox[0].to == ["organizer@example.com"]
    assert mail.outbox[0].subject == subject_str.format("organizer", event.name)
    assert mail.outbox[1].subject == subject_str.format("contractor", event.name)
    assert mail.outbox[2].subject == subject_str.format("contractor", event.name)
    assert mail.outbox[3].subject == subject_str.format("official", event.name)

    assert_to_addresses(
        event.organizer_email,
        contract_zone.email,
        contract_zone.secondary_email,
        official.email,
    )


@pytest.mark.parametrize("vacation_involved", (True, False))
def test_event_reminder_notification_is_sent_to_contractors_in_time(
    notification_template_event_reminder, vacation_involved
):

    if vacation_involved:
        # now = Friday, events on Tuesday should be the latest to get the reminder
        current_moment = "2018-01-12T08:00:00Z"
        event_days_afterwards = 4
    else:
        # now = Wednesday, events on Friday should be the latest to get the reminder
        current_moment = "2018-01-10T08:00:00Z"
        event_days_afterwards = 2

    freezer = freeze_time(current_moment)
    freezer.start()

    # this time should be 1 minute too far in the future
    start_time = localtime(now() + timedelta(days=event_days_afterwards + 1)).replace(
        hour=0, minute=1
    )
    event = EventFactory(state=Event.APPROVED, start_time=start_time)

    call_command("send_event_reminder_notifications")
    assert len(mail.outbox) == 0

    # this time should be inside by 1 minute
    event.start_time -= timedelta(minutes=2)
    event.save()

    call_command("send_event_reminder_notifications")

    assert len(mail.outbox) == 2
    subject_str = "hello! don't forget event {}!".format(event.name)
    assert mail.outbox[0].subject == subject_str
    assert mail.outbox[1].subject == subject_str
    assert_to_addresses(event.contract_zone.email, event.contract_zone.secondary_email)

    freezer.stop()
