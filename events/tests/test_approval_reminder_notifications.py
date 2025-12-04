"""
Tests for the send_approval_reminder_notifications management command.

This command sends reminder notifications to contractors about pending events
that need approval, with two independent triggers:
1. Creation-based: X days after the event was created
2. Deadline-based: Y days before the event is scheduled to start
"""

from datetime import timedelta

import pytest
from django.conf import settings
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
def notification_template():
    return NotificationTemplate.objects.language("fi").create(
        type=NotificationType.EVENT_PENDING_APPROVAL_REMINDER.value,
        subject="please approve event {{ event.name }}!",
        body_html="<b>test pending approval reminder body HTML!</b>",
        body_text="test pending approval reminder body text!",
    )


class TestCreationBasedReminder:
    """Tests for the creation-based approval reminder (X days after event creation)."""

    def test_reminder_sent_on_exact_day(self, notification_template):
        """
        Reminder should be sent exactly APPROVAL_REMINDER_DAYS_AFTER_CREATION days
        after the event was created (on a business day).
        """
        # Create event on Monday 2018-01-08
        # Reminder should fire 3 days later = Thursday 2018-01-11 (business day)
        with freeze_time("2018-01-08T08:00:00Z"):  # Monday
            contract_zone = ContractZoneFactory(
                email="primary@test.test", secondary_email="secondary@test.test"
            )
            event = EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=now() + timedelta(days=30),  # Far in future
            )
            mail.outbox = []

            # Should not send on day of creation
            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 0

        # Advance to 3 days later (Thursday 2018-01-11)
        with freeze_time("2018-01-11T08:00:00Z"):  # Thursday
            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 2
            assert_to_addresses(contract_zone.email, contract_zone.secondary_email)
            assert mail.outbox[0].subject == f"please approve event {event.name}!"

    def test_vacation_day_shifts_to_next_business_day(self, notification_template):
        """
        If the creation reminder falls on a weekend, it should shift to the
        NEXT business day (Monday), ensuring contractors have the full waiting period.
        """
        # Create event on Thursday 2018-01-11
        # Reminder would be 3 days later = Sunday 2018-01-14 (vacation day)
        # Should shift FORWARD to Monday 2018-01-15
        with freeze_time("2018-01-11T08:00:00Z"):  # Thursday
            contract_zone = ContractZoneFactory(
                email="contractor@test.test", secondary_email=""
            )
            event = EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=now() + timedelta(days=30),
            )
            mail.outbox = []

        # Sunday 2018-01-14 - should NOT fire (shifted to Monday)
        with freeze_time("2018-01-14T08:00:00Z"):  # Sunday
            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 0

        # Monday 2018-01-15 - should fire
        with freeze_time("2018-01-15T08:00:00Z"):  # Monday
            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 1
            assert mail.outbox[0].subject == f"please approve event {event.name}!"

    def test_reminder_not_sent_for_approved_events(self, notification_template):
        """Approved events should not receive approval reminders."""
        with freeze_time("2018-01-08T08:00:00Z"):  # Monday
            contract_zone = ContractZoneFactory(email="contractor@test.test")
            EventFactory(
                state=Event.APPROVED,  # Already approved
                contract_zone=contract_zone,
                start_time=now() + timedelta(days=30),
            )
            mail.outbox = []

        # 3 days later (Thursday)
        with freeze_time("2018-01-11T08:00:00Z"):
            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 0

    def test_reminder_disabled_with_negative_value(
        self, notification_template, settings
    ):
        """Setting APPROVAL_REMINDER_DAYS_AFTER_CREATION to -1 disables this reminder."""
        settings.APPROVAL_REMINDER_DAYS_AFTER_CREATION = -1

        with freeze_time("2018-01-08T08:00:00Z"):  # Monday
            contract_zone = ContractZoneFactory(email="contractor@test.test")
            EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=now() + timedelta(days=30),
            )
            mail.outbox = []

        # 3 days later - should not fire because disabled
        with freeze_time("2018-01-11T08:00:00Z"):
            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 0


class TestDeadlineBasedReminder:
    """Tests for the deadline-based approval reminder (Y days before event start)."""

    def test_reminder_sent_on_exact_day_before_event(self, notification_template):
        """
        Reminder should be sent exactly APPROVAL_REMINDER_DAYS_BEFORE_EVENT days
        before the event starts.
        """
        # now = Monday 2018-01-08
        # Event starts in 5 days = Saturday 2018-01-13
        # Deadline reminder = 5 days before = Monday 2018-01-08 (today)
        with freeze_time("2018-01-08T08:00:00Z"):  # Monday
            contract_zone = ContractZoneFactory(
                email="primary@test.test", secondary_email="secondary@test.test"
            )
            event = EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=now()
                + timedelta(days=settings.APPROVAL_REMINDER_DAYS_BEFORE_EVENT),
            )
            mail.outbox = []

            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 2
            assert_to_addresses(contract_zone.email, contract_zone.secondary_email)
            assert mail.outbox[0].subject == f"please approve event {event.name}!"

    def test_reminder_not_sent_before_deadline_reminder_day(
        self, notification_template
    ):
        """Reminder should not be sent before the deadline reminder day."""
        # now = Monday 2018-01-08
        # Event starts in 10 days = Thursday 2018-01-18
        # Deadline reminder = 5 days before = Saturday 2018-01-13, shifts to Friday 2018-01-12
        with freeze_time("2018-01-08T08:00:00Z"):
            contract_zone = ContractZoneFactory(email="contractor@test.test")
            EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=now() + timedelta(days=10),
            )
            mail.outbox = []

            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 0

    def test_vacation_day_shifts_to_preceding_business_day(self, notification_template):
        """
        If the deadline reminder falls on a weekend, it should shift to the
        PRECEDING business day (Friday), to ensure reminder is sent in time.
        """
        # Event starts on Thursday 2018-01-18
        # Deadline reminder = 5 days before = Saturday 2018-01-13 (vacation day)
        # Should shift BACKWARD to Friday 2018-01-12
        with freeze_time("2018-01-12T08:00:00Z"):  # Friday
            contract_zone = ContractZoneFactory(
                email="contractor@test.test", secondary_email=""
            )
            event = EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=localtime(now()).replace(
                    year=2018, month=1, day=18, hour=10, minute=0
                ),  # Thursday
            )
            mail.outbox = []

            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 1
            assert mail.outbox[0].subject == f"please approve event {event.name}!"

    def test_reminder_disabled_with_negative_value(
        self, notification_template, settings
    ):
        """Setting APPROVAL_REMINDER_DAYS_BEFORE_EVENT to -1 disables this reminder."""
        settings.APPROVAL_REMINDER_DAYS_BEFORE_EVENT = -1

        with freeze_time("2018-01-08T08:00:00Z"):
            contract_zone = ContractZoneFactory(email="contractor@test.test")
            EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=now() + timedelta(days=5),  # Would normally trigger
            )
            mail.outbox = []

            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 0


class TestBothTriggers:
    """Tests for scenarios where both triggers might fire."""

    def test_both_reminders_can_fire_independently(self, notification_template):
        """
        Both creation-based and deadline-based reminders should be able to fire
        for the same event on different days.
        """
        # Create event on Monday 2018-01-08
        # Event starts on Monday 2018-01-22 (14 days later)
        # Creation reminder: 2018-01-08 + 3 = Thursday 2018-01-11
        # Deadline reminder: 2018-01-22 - 5 = Wednesday 2018-01-17
        with freeze_time("2018-01-08T08:00:00Z"):  # Monday
            contract_zone = ContractZoneFactory(
                email="contractor@test.test", secondary_email=""
            )
            event = EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=localtime(now()).replace(
                    year=2018, month=1, day=22, hour=10, minute=0
                ),  # Monday 2018-01-22
            )
            mail.outbox = []

        # Day 3 (Thursday 2018-01-11) - creation reminder fires
        with freeze_time("2018-01-11T08:00:00Z"):
            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 1
            assert mail.outbox[0].subject == f"please approve event {event.name}!"
            mail.outbox = []

        # 5 days before event (Wednesday 2018-01-17) - deadline reminder fires
        with freeze_time("2018-01-17T08:00:00Z"):
            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 1
            assert mail.outbox[0].subject == f"please approve event {event.name}!"

    def test_both_reminders_fire_on_same_day_if_dates_align(
        self, notification_template
    ):
        """
        If creation and deadline reminder days are the same, only one reminder
        should be sent (since it's the same notification).
        """
        # Create event on Monday 2018-01-08
        # Event starts Tuesday 2018-01-16 (8 days later)
        # Creation reminder: 2018-01-08 + 3 = Thursday 2018-01-11
        # Deadline reminder: 2018-01-16 - 5 = Thursday 2018-01-11
        # Both align on Thursday 2018-01-11
        with freeze_time("2018-01-08T08:00:00Z"):  # Monday
            contract_zone = ContractZoneFactory(
                email="contractor@test.test", secondary_email=""
            )
            event = EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=localtime(now()).replace(
                    year=2018, month=1, day=16, hour=10, minute=0
                ),  # Tuesday 2018-01-16
            )
            mail.outbox = []

        # Thursday 2018-01-11 - both triggers match, but only one email sent
        with freeze_time("2018-01-11T08:00:00Z"):
            call_command("send_approval_reminder_notifications")
            # Even though both conditions match, we only send one notification
            assert len(mail.outbox) == 1
            assert mail.outbox[0].subject == f"please approve event {event.name}!"

    def test_both_reminders_disabled(self, notification_template, settings):
        """When both reminders are disabled, no emails are sent."""
        settings.APPROVAL_REMINDER_DAYS_AFTER_CREATION = -1
        settings.APPROVAL_REMINDER_DAYS_BEFORE_EVENT = -1

        with freeze_time("2018-01-08T08:00:00Z"):
            contract_zone = ContractZoneFactory(email="contractor@test.test")
            EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=now() + timedelta(days=5),
            )
            mail.outbox = []

            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 0


class TestEdgeCases:
    """Edge case tests for approval reminders."""

    def test_no_reminder_for_past_events(self, notification_template):
        """Events that have already started should not receive reminders."""
        with freeze_time("2018-01-14T08:00:00Z"):
            contract_zone = ContractZoneFactory(email="contractor@test.test")
            # Event that started yesterday
            EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=now() - timedelta(days=1),
            )
            mail.outbox = []

            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 0

    def test_no_reminder_when_contract_zone_has_no_email(
        self, notification_template, caplog
    ):
        """When contract zone has no email, log a warning and don't crash."""
        with freeze_time("2018-01-10T08:00:00Z"):
            contract_zone = ContractZoneFactory(email="", secondary_email="")
            EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone,
                start_time=now()
                + timedelta(days=settings.APPROVAL_REMINDER_DAYS_BEFORE_EVENT),
            )
            mail.outbox = []

            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 0
            assert "has no contact email" in caplog.text

    def test_multiple_pending_events_each_get_reminders(self, notification_template):
        """Each pending event should be evaluated independently."""
        with freeze_time("2018-01-10T08:00:00Z"):
            contract_zone1 = ContractZoneFactory(
                email="contractor1@test.test", secondary_email=""
            )
            contract_zone2 = ContractZoneFactory(
                email="contractor2@test.test", secondary_email=""
            )

            # Both events have deadline reminder today
            EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone1,
                start_time=now()
                + timedelta(days=settings.APPROVAL_REMINDER_DAYS_BEFORE_EVENT),
            )
            EventFactory(
                state=Event.WAITING_FOR_APPROVAL,
                contract_zone=contract_zone2,
                start_time=now()
                + timedelta(days=settings.APPROVAL_REMINDER_DAYS_BEFORE_EVENT),
            )
            mail.outbox = []

            call_command("send_approval_reminder_notifications")
            assert len(mail.outbox) == 2
            assert_to_addresses(contract_zone1.email, contract_zone2.email)
