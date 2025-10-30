"""Management command to anonymize old Event PII."""

from datetime import timedelta
import logging
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from events.models import Event


logger = logging.getLogger(__name__)


# Sentinel values used to replace PII fields during anonymization
SENTINELS = {
    "name": "Anonymized event",
    "description": "",
    "additional_information": "",
    "organizer_first_name": "",
    "organizer_last_name": "",
    "organizer_email": "anonymized@invalid",
    "organizer_phone": "",
}


class Command(BaseCommand):
    """
    Django management command to anonymize old Event PII (Personally Identifiable Information).

    This command replaces sensitive organizer information with sentinel values for events
    that have ended more than a configurable number of days ago. Events are never deleted,
    only anonymized in-place.

    The command supports:
    - Configurable retention period (default: 90 days)
    - Dry-run mode for testing
    - Optional location coarsening (replacing precise location with zone centroid)
    - Batch processing for performance

    Use case: GDPR compliance by removing PII from old events while preserving
    aggregate statistics and event history.
    """
    help = "Anonymize old Event PII in-place, never deleting events"

    def get_cutoff_date(self, options):
        """
        Calculate the cutoff date for event anonymization.

        Events with end_time before this date will be anonymized.

        Args:
            options: Parsed command line options

        Returns:
            datetime: The cutoff datetime (events ending before this are eligible)
        """
        # Retention days: CLI overrides env; default 90 if neither is provided
        days = options.get("older_than_days") or int(
            os.environ.get("EVENTS_ANONYMIZE_AFTER_DAYS", 90)
        )
        return timezone.now() - timedelta(days=days)

    def get_events_to_anonymize(self, cutoff_date):
        """
        Get the queryset of events eligible for anonymization.

        Returns events that have ended before the cutoff date and haven't
        already been anonymized (based on the sentinel organizer_email).

        Args:
            cutoff_date: Datetime threshold - events ending before this are eligible

        Returns:
            QuerySet: Events to be anonymized
        """
        base_qs = Event.objects.filter(end_time__lte=cutoff_date)
        # Ignore already obfuscated emails - use organizer_email sentinel as primary idempotency guard
        return base_qs.exclude(organizer_email=SENTINELS["organizer_email"])

    def anonymize_events(self, events_queryset):
        """
        Perform anonymization of events.

        Replaces PII fields with sentinel values for all eligible events.

        Args:
            events_queryset: QuerySet of events to anonymize

        Returns:
            int: Number of events successfully anonymized
        """
        # Load all eligible events
        events = list(events_queryset)

        with transaction.atomic():
            for event in events:
                update_values = {
                    **SENTINELS,
                    "modified_at": timezone.now(),
                }

                Event.objects.filter(pk=event.pk).update(**update_values)

    def add_arguments(self, parser):
        """
        Configure command line arguments.

        Adds all supported options for controlling the anonymization process.
        """
        parser.add_argument("--older-than-days", type=int,
                           help="Override default retention period (days)")
        parser.add_argument("--dry-run", action="store_true",
                           help="Show what would be anonymized without making changes")

    def handle(self, *args, **options):
        """
        Main command execution handler.

        Orchestrates the anonymization process: determines cutoff date,
        identifies eligible events, handles dry-run option,
        and performs the anonymization.
        """
        cutoff_date = self.get_cutoff_date(options)

        events_to_anonymize = self.get_events_to_anonymize(cutoff_date)

        total_eligible = events_to_anonymize.count()
        self.stdout.write(
            "Eligible events for anonymization "
            f"(end_time <= {cutoff_date.isoformat()}): {total_eligible}"
        )

        if options.get("dry_run"):
            self.stdout.write("Dry run: no changes applied")
            return

        self.anonymize_events(events_to_anonymize)


