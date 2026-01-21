"""
Management command to send approval reminder notifications to contractors.

This command should be run daily via a scheduled task (e.g., cron job).
It sends reminders to contractors about pending events that need approval,
based on two independent triggers:

1. Creation-based: X days after the event was created (shifts to next business day
   if it falls on a vacation day, to ensure contractors have the full time period)
2. Deadline-based: Y days before the event is scheduled to start (shifts to preceding
   business day if it falls on a vacation day, to ensure reminder is sent in time)

Both triggers use exact date matching. Per-trigger timestamps are stored to
prevent duplicate sends if the job reruns on the same day (e.g. crash loops).

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
            creation_due = self._is_creation_reminder_due(event, today)
            deadline_due = self._is_deadline_reminder_due(event, today)

            # If neither trigger is due (or already sent), skip
            if not (creation_due or deadline_due):
                continue

            sent = send_pending_approval_reminder_notification(event)
            if not sent:
                # Leave timestamps untouched
                # so a later run can try again if data is fixed
                continue

            timestamp = now()
            update_fields = []
            if creation_due:
                event.approval_creation_reminder_sent_at = timestamp
                update_fields.append("approval_creation_reminder_sent_at")
            if deadline_due:
                event.approval_deadline_reminder_sent_at = timestamp
                update_fields.append("approval_deadline_reminder_sent_at")

            if update_fields:
                event.save(update_fields=update_fields)

            reminders_sent += 1
            logger.info(
                f"Sent approval reminder for event '{event.name}' (ID: {event.pk})"
            )

        logger.info(
            f"Approval reminder check complete. Sent {reminders_sent} reminder(s)"
        )

    def _is_creation_reminder_due(self, event, today):
        """
        Return True when the creation-based reminder should send today and has
        not already been sent (timestamp is null).
        """
        reminder_day = self._calculate_creation_reminder_day(event)
        if reminder_day is None or event.approval_creation_reminder_sent_at:
            return False
        return today == reminder_day

    def _is_deadline_reminder_due(self, event, today):
        """
        Return True when the deadline-based reminder should send today and has
        not already been sent (timestamp is null).
        """
        reminder_day = self._calculate_deadline_reminder_day(event)
        if reminder_day is None or event.approval_deadline_reminder_sent_at:
            return False
        return today == reminder_day

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
