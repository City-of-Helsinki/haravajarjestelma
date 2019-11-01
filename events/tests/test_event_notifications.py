from datetime import timedelta

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils.timezone import localtime, now
from django_ilmoitin.models import NotificationTemplate
from freezegun import freeze_time

from events.factories import EventFactory
from events.models import Event
from events.notifications import NotificationType


@pytest.fixture
def notification_template_event_created():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_CREATED,
        subject="test event created subject, event: {{ event.name }}! user is official: {{ user.is_official }}!",
        body_html="<b>test event created body HTML!</b>",
        body_text="test event created body text!",
    )


@pytest.fixture
def notification_template_event_approved_to_organizer():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_APPROVED_TO_ORGANIZER,
        subject="hello organizer! event {{ event.name }} approved!",
        body_html="<b>test event approved body HTML!</b>",
        body_text="test event approved body text!",
    )


@pytest.fixture
def notification_template_event_approved_to_contractor():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_APPROVED_TO_CONTRACTOR,
        subject="hello contractor! event {{ event.name }} approved!",
        body_html="<b>test event approved body HTML!</b>",
        body_text="test event approved body text!",
    )


@pytest.fixture
def notification_template_event_approved_to_official():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_APPROVED_TO_OFFICIAL,
        subject="hello official! event {{ event.name }} approved!",
        body_html="<b>test event approved body HTML!</b>",
        body_text="test event approved body text!",
    )


@pytest.fixture
def notification_template_event_reminder():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_REMINDER,
        subject="hello {{ user.first_name }}! don't forget event {{ event.name }}!",
        body_html="<b>test event reminder body HTML!</b>",
        body_text="test event reminder body text!",
    )


def test_event_created_notification_is_sent_to_contractor_and_admin(
    contract_zone, user, notification_template_event_created, official
):
    contract_zone.contractor_user = user
    contract_zone.save(update_fields=("contractor_user",))

    event = EventFactory()

    assert len(mail.outbox) == 2
    subject_str = "test event created subject, event: {}! user is official: {}!"
    assert mail.outbox[0].subject == subject_str.format(event.name, False)
    assert mail.outbox[1].subject == subject_str.format(event.name, True)


def test_event_created_notification_is_not_sent_to_other_contractor(
    contract_zone, user, notification_template_event_created
):
    assert contract_zone.contractor_user != user

    EventFactory()

    assert len(mail.outbox) == 0


def test_notification_is_not_sent_when_event_modified_or_deleted(
    contract_zone, user, notification_template_event_created
):
    contract_zone.contractor_user = user
    contract_zone.save(update_fields=("contractor_user",))
    event = EventFactory()
    mail.outbox = []

    event.name = "foobar"
    event.save(update_fields=("name",))
    assert len(mail.outbox) == 0

    event.delete()
    assert len(mail.outbox) == 0


def test_event_approved_to_organizer_notification_is_sent_to_organizer_and_contractor_and_official(
    contract_zone,
    user,
    notification_template_event_approved_to_organizer,
    notification_template_event_approved_to_contractor,
    notification_template_event_approved_to_official,
    contractor,
    official,
):
    contract_zone.contractor_user = contractor
    contract_zone.save(update_fields=("contractor_user",))

    event = EventFactory(
        state=Event.WAITING_FOR_APPROVAL, organizer_email="organizer@example.com"
    )
    mail.outbox = []
    event.state = Event.APPROVED
    event.save()

    assert len(mail.outbox) == 3
    subject_str = "hello {}! event {} approved!"

    assert mail.outbox[0].to == ["organizer@example.com"]
    assert mail.outbox[0].subject == subject_str.format("organizer", event.name)
    assert mail.outbox[1].subject == subject_str.format("contractor", event.name)
    assert mail.outbox[2].subject == subject_str.format("official", event.name)


@pytest.mark.parametrize("vacation_involved", (True, False))
def test_event_reminder_notification_is_sent_to_contractor_in_time(
    contract_zone, contractor, notification_template_event_reminder, vacation_involved
):
    contract_zone.contractor_user = contractor
    contract_zone.save(update_fields=("contractor_user",))

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

    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "hello {}! don't forget event {}!".format(
        contractor.first_name, event.name
    )

    freezer.stop()
