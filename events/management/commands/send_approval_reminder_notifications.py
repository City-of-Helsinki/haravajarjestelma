"""
Management command to send approval reminder notifications to contractors.

This command should be run daily via a scheduled task (e.g., cron job).
It sends reminders to contractors about pending events that need approval,
based on two independent triggers:

1. Creation-based: X days after the event was created (shifts to next business day
   if it falls on a vacation day, to ensure contractors have the full time period)
2. Deadline-based: Y days before the event is scheduled to start (shifts to preceding
   business day if it falls on a vacation day, to ensure reminder is sent in time)

Both triggers use exact date matching, so the command naturally prevents
duplicate emails when run daily.

Set either APPROVAL_REMINDER_DAYS_AFTER_CREATION or APPROVAL_REMINDER_DAYS_BEFORE_EVENT
to -1 to disable that particular reminder type.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import localtime, now

from common.utils import ONE_DAY, get_today, is_vacation_day
from events.models import Event
from events.notifications import send_pending_approval_reminder_notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send approval reminder notifications to contractors for pending events"

    def handle(self, *args, **options):
        logger.info("Checking for pending events that need approval reminders")
        today = get_today()
        reminders_sent = 0

        # Query only pending events that haven't started yet
        pending_events = Event.objects.filter(
            state=Event.WAITING_FOR_APPROVAL,
            start_time__gt=now(),
        )

        for event in pending_events:
            should_send = self._should_send_reminder(event, today)
            if should_send:
                send_pending_approval_reminder_notification(event)
                reminders_sent += 1
                logger.info(
                    f"Sent approval reminder for event '{event.name}' (ID: {event.pk})"
                )

        logger.info(f"Approval reminder check complete. Sent {reminders_sent} reminder(s)")

    def _should_send_reminder(self, event, today):
        """
        Determine if an approval reminder should be sent for the given event.

        Returns True if today matches either:
        - The creation-based reminder day (X days after event creation)
        - The deadline-based reminder day (Y days before event start)

        Either reminder type can be disabled by setting its config value to -1.
        """
        creation_reminder_day = self._calculate_creation_reminder_day(event)
        deadline_reminder_day = self._calculate_deadline_reminder_day(event)

        creation_match = creation_reminder_day is not None and today == creation_reminder_day
        deadline_match = deadline_reminder_day is not None and today == deadline_reminder_day

        return creation_match or deadline_match

    def _calculate_creation_reminder_day(self, event):
        """
        Calculate the day to send a creation-based reminder.

        The reminder is scheduled for X days after the event was created.
        If this falls on a vacation day (weekend or Finnish holiday), the reminder
        is shifted to the NEXT business day. This ensures contractors have the
        full waiting period before receiving the reminder.

        Returns None if this reminder type is disabled (configured as -1).
        """
        days_after = settings.APPROVAL_REMINDER_DAYS_AFTER_CREATION
        if days_after < 0:
            return None

        reminder_day = localtime(event.created_at).date() + timedelta(days=days_after)

        # Shift to next business day if reminder falls on vacation
        while is_vacation_day(reminder_day):
            reminder_day += ONE_DAY

        return reminder_day

    def _calculate_deadline_reminder_day(self, event):
        """
        Calculate the day to send a deadline-based reminder.

        The reminder is scheduled for Y days before the event starts.
        If this falls on a vacation day (weekend or Finnish holiday), the reminder
        is shifted to the PRECEDING business day. This ensures the reminder is
        sent before the deadline passes.

        Returns None if this reminder type is disabled (configured as -1).
        """
        days_before = settings.APPROVAL_REMINDER_DAYS_BEFORE_EVENT
        if days_before < 0:
            return None

        reminder_day = localtime(event.start_time).date() - timedelta(days=days_before)

        # Shift to preceding business day if reminder falls on vacation
        while is_vacation_day(reminder_day):
            reminder_day -= ONE_DAY

        return reminder_day
