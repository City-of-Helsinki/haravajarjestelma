"""
Dummy context for django-ilmoitin email template development.

This module provides sample data for email templates used by django-ilmoitin,
the project's email notification system. The dummy context enables template
previews in Django admin and provides realistic test data during development.

We extend django-ilmoitin's global dummy_context with:
- COMMON_CONTEXT: Site-wide variables available in all email templates
- Template-specific sample data for each notification type
"""

from django_ilmoitin.dummy_context import COMMON_CONTEXT, dummy_context
from areas.factories import ContractZoneFactory
from .factories import EventFactory

# Import the base context function for consistent context
from .notifications import get_notification_base_context

# Create sample contract zone for template development
sample_zone = ContractZoneFactory.build(
    name="Keskuspuisto",
    email="keskuspuisto@hel.fi"
)

# Create sample event for template development
sample_event = EventFactory.build(
    contract_zone=sample_zone,
    name="Sample Park Cleanup Event",
    description="Let's clean up the park together! We'll meet at the main entrance and work our way through the park collecting litter.",
    organizer_email="organizer@example.com",
    organizer_first_name="John",
    organizer_last_name="Doe",
    organizer_phone="+358 50 123 4567",
    start_time="2024-12-25T10:00:00Z",
    end_time="2024-12-25T14:00:00Z",
    estimated_attendee_count=15,
    targets="Clean up litter from park paths and picnic areas",
    maintenance_location="Central Park, Helsinki",
    additional_information="Please bring your own gloves if possible. Coffee and snacks will be provided.",
    small_trash_bag_count=20,
    large_trash_bag_count=5,
    trash_picker_count=10,
    equipment_information="Additional trash bags will be provided by the city",
)


# Update dummy context with sample data
dummy_context.update({
    COMMON_CONTEXT: get_notification_base_context(),
    "event_received": {
        "event": sample_event,
    },
})
