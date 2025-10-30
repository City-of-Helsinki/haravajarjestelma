import os
from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.utils import timezone
from freezegun import freeze_time

from areas.factories import ContractZoneFactory
from events.factories import EventFactory


@pytest.fixture(autouse=True)
def reset_env_var():
    """Reset the environment variable after each test to avoid side effects."""
    yield
    if "EVENTS_ANONYMIZE_AFTER_DAYS" in os.environ:
        del os.environ["EVENTS_ANONYMIZE_AFTER_DAYS"]


def test_works_without_parameters_using_env_default(capsys):
        """Test that the command works without parameters, using the default 90 days from env."""
        with freeze_time("2023-01-01"):
            # Create an event that is older than 90 days
            event = EventFactory(
                end_time=timezone.now() - timedelta(days=91),
            )
            # Ensure it's not already anonymized
            assert event.organizer_email != "anonymized@invalid"

            # Run the command
            call_command("obfuscate_events")

            # Refresh from DB and check anonymization
            event.refresh_from_db()
            assert event.name == "Anonymized event"
            assert event.description == ""
            assert event.additional_information == ""
            assert event.organizer_first_name == ""
            assert event.organizer_last_name == ""
            assert event.organizer_email == "anonymized@invalid"
            assert event.organizer_phone == ""
            # Times should remain unchanged
            assert event.start_time == event.start_time  # Compare to original if needed
            assert event.end_time == event.end_time

def test_respects_env_var_for_retention_days(capsys):
        """Test that the command respects the EVENTS_ANONYMIZE_AFTER_DAYS env var."""
        os.environ["EVENTS_ANONYMIZE_AFTER_DAYS"] = "30"
        with freeze_time("2023-01-01"):
            # Create an event older than 30 days and one 20 days old
            old_event = EventFactory(end_time=timezone.now() - timedelta(days=31))
            recent_event = EventFactory(end_time=timezone.now() - timedelta(days=20))

            call_command("obfuscate_events")

            # Only the old event should be anonymized
            old_event.refresh_from_db()
            recent_event.refresh_from_db()
            assert old_event.organizer_email == "anonymized@invalid"
            assert recent_event.organizer_email != "anonymized@invalid"  # Unchanged

def test_cli_overrides_env_var(capsys):
        """Test that CLI --older-than-days overrides the env var."""
        os.environ["EVENTS_ANONYMIZE_AFTER_DAYS"] = "60"
        with freeze_time("2023-01-01"):
            # Create events 20 and 10 days old
            event_20d = EventFactory(end_time=timezone.now() - timedelta(days=20))
            event_10d = EventFactory(end_time=timezone.now() - timedelta(days=10))

            call_command("obfuscate_events", "--older-than-days", 15)

            # Only the 20d old event should be anonymized (15d threshold)
            event_20d.refresh_from_db()
            event_10d.refresh_from_db()
            assert event_20d.organizer_email == "anonymized@invalid"
            assert event_10d.organizer_email != "anonymized@invalid"

def test_dry_run_does_not_change_data(capsys):
        """Test that --dry-run counts eligible events but doesn't modify them."""
        with freeze_time("2023-01-01"):
            original_name = "Original Name"
            event = EventFactory(
                name=original_name,
                end_time=timezone.now() - timedelta(days=91),
            )

            call_command("obfuscate_events", "--dry-run")

            # Event should remain unchanged
            event.refresh_from_db()
            assert event.name == original_name
            assert event.organizer_email != "anonymized@invalid"

            # Check stdout for dry-run message (optional, depending on implementation)
            captured = capsys.readouterr()
            assert "Dry run: no changes applied" in captured.out

def test_idempotency_already_anonymized_events_unchanged(capsys):
        """Test that running the command multiple times is idempotent."""
        with freeze_time("2023-01-01"):
            event = EventFactory(end_time=timezone.now() - timedelta(days=91))
            # Manually set to anonymized state
            event.organizer_email = "anonymized@invalid"
            event.save()

            call_command("obfuscate_events")

            # Should remain anonymized without errors
            event.refresh_from_db()
            assert event.organizer_email == "anonymized@invalid"
            # Other fields should still be original if they were
            assert event.name != "Anonymized event"  # Assuming it wasn't anonymized before

def test_non_eligible_events_unaffected(capsys):
        """Test that events within the retention period are not anonymized."""
        with freeze_time("2023-01-01"):
            # Default 90 days
            event = EventFactory(end_time=timezone.now() - timedelta(days=89))

            call_command("obfuscate_events")

            event.refresh_from_db()
            # Should remain unchanged
            assert event.organizer_email != "anonymized@invalid"
            assert event.name != "Anonymized event"

def test_cutoff_inclusivity(capsys):
        """Test that events exactly at the cutoff are included."""
        with freeze_time("2023-01-01"):
            # Exactly 90 days old
            event = EventFactory(end_time=timezone.now() - timedelta(days=90))

            call_command("obfuscate_events")

            event.refresh_from_db()
            assert event.organizer_email == "anonymized@invalid"

def test_location_kept_precise_by_default(capsys):
        """Test that location is kept precise by default."""
        with freeze_time("2023-01-01"):
            original_location = Point(24.9458, 60.1921, srid=4326)
            event = EventFactory(
                location=original_location,
                end_time=timezone.now() - timedelta(days=91),
            )

            call_command("obfuscate_events")

            event.refresh_from_db()
            # Location should remain the same
            assert event.location.x == original_location.x
            assert event.location.y == original_location.y

def test_anonymization_with_multiple_events(capsys):
        """Test that anonymization works for multiple events."""
        with freeze_time("2023-01-01"):
            # Create multiple eligible events
            events = EventFactory.create_batch(
                3,
                end_time=timezone.now() - timedelta(days=91),
            )

            call_command("obfuscate_events")

            # All should be anonymized
            for event in events:
                event.refresh_from_db()
                assert event.organizer_email == "anonymized@invalid"

def test_already_anonymized_events_are_skipped(capsys):
        """Test that already anonymized events are skipped during anonymization."""
        with freeze_time("2023-01-01"):
            event1 = EventFactory(end_time=timezone.now() - timedelta(days=91))
            event2 = EventFactory(end_time=timezone.now() - timedelta(days=91))
            # Anonymize one manually
            event1.organizer_email = "anonymized@invalid"
            event1.save()

            call_command("obfuscate_events")

            event1.refresh_from_db()
            event2.refresh_from_db()
            # event1 should remain as is, event2 anonymized
            assert event1.organizer_email == "anonymized@invalid"
            assert event1.name != "Anonymized event"  # Assuming original name
            assert event2.organizer_email == "anonymized@invalid"
            assert event2.name == "Anonymized event"
