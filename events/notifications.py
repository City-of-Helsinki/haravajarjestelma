import logging
from enum import Enum

from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_ilmoitin.registry import notifications
from django_ilmoitin.utils import send_notification

User = get_user_model()

logger = logging.getLogger(__name__)


def get_notification_base_context():
    """Get common context variables for all notifications"""
    return {
        "site_name": "Helsinki Puistotalkoot",
        "site_url": "https://puistotalkoot.hel.fi",
    }


class NotificationType(Enum):
    EVENT_CREATED = ("event_created", _("Event created"))
    EVENT_RECEIVED = ("event_received", _("Event received confirmation"))
    EVENT_APPROVED_TO_ORGANIZER = (
        "event_approved_to_organizer",
        _("Event approved notification to organizer"),
    )
    EVENT_APPROVED_TO_CONTRACTOR = (
        "event_approved_to_contractor",
        _("Event approved notification to contractor"),
    )
    EVENT_APPROVED_TO_OFFICIAL = (
        "event_approved_to_official",
        _("Event approved notification to official"),
    )
    EVENT_REMINDER = ("event_reminder", _("Event reminder"))
    EVENT_PENDING_APPROVAL_REMINDER = (
        "event_pending_approval_reminder",
        _("Event pending approval reminder"),
    )

    def __init__(self, value, label) -> None:
        self._value_ = value
        self.label = label


notifications.register(
    NotificationType.EVENT_CREATED.value, NotificationType.EVENT_CREATED.label
)
notifications.register(
    NotificationType.EVENT_RECEIVED.value, NotificationType.EVENT_RECEIVED.label
)
notifications.register(
    NotificationType.EVENT_APPROVED_TO_ORGANIZER.value,
    NotificationType.EVENT_APPROVED_TO_ORGANIZER.label,
)
notifications.register(
    NotificationType.EVENT_APPROVED_TO_CONTRACTOR.value,
    NotificationType.EVENT_APPROVED_TO_CONTRACTOR.label,
)
notifications.register(
    NotificationType.EVENT_APPROVED_TO_OFFICIAL.value,
    NotificationType.EVENT_APPROVED_TO_OFFICIAL.label,
)
notifications.register(
    NotificationType.EVENT_REMINDER.value, NotificationType.EVENT_REMINDER.label
)
notifications.register(
    NotificationType.EVENT_PENDING_APPROVAL_REMINDER.value,
    NotificationType.EVENT_PENDING_APPROVAL_REMINDER.label,
)


def send_event_created_notification(event):
    _send_notifications_to_contractor_and_officials(
        event, NotificationType.EVENT_CREATED.value
    )


def send_event_received_notification(event):
    """Send event received confirmation to the organizer"""
    context = get_notification_base_context()
    context["event"] = event
    send_notification(
        event.organizer_email,
        NotificationType.EVENT_RECEIVED.value,
        context,
    )


def send_event_approved_notification(event):
    context = get_notification_base_context()
    context["event"] = event
    send_notification(
        event.organizer_email,
        NotificationType.EVENT_APPROVED_TO_ORGANIZER.value,
        context,
    )
    _send_notifications_to_contractor_and_officials(
        event,
        NotificationType.EVENT_APPROVED_TO_CONTRACTOR.value,
        NotificationType.EVENT_APPROVED_TO_OFFICIAL.value,
    )


def send_event_reminder_notification(event):
    contact_emails = event.contract_zone.get_contact_emails()

    if not contact_emails:
        logger.warning(
            f"Contract zone {event.contract_zone} has no contact email so cannot send "
            '"event_reminder" notification there.'
        )
        return

    context = get_notification_base_context()
    context["event"] = event
    for email in contact_emails:
        send_notification(email, NotificationType.EVENT_REMINDER.value, context)

    event.reminder_sent_at = now()
    event.save(update_fields=("reminder_sent_at",))


def send_pending_approval_reminder_notification(event):
    """
    Send a reminder to contractors that an event is awaiting their approval.

    This notification is sent to remind contractors to approve or decline
    pending events before the deadline.
    """
    contact_emails = event.contract_zone.get_contact_emails()

    if not contact_emails:
        logger.warning(
            f"Contract zone {event.contract_zone} has no contact email so cannot send "
            '"event_pending_approval_reminder" notification there.'
        )
        return

    for email in contact_emails:
        send_notification(
            email,
            NotificationType.EVENT_PENDING_APPROVAL_REMINDER.value,
            {"event": event},
        )


def _send_notifications_to_contractor_and_officials(
    event, notification_type_contractor, notification_type_official=None
):
    if not notification_type_official:
        notification_type_official = notification_type_contractor

    context = get_notification_base_context()
    context["event"] = event

    contact_emails = event.contract_zone.get_contact_emails()
    if contact_emails:
        for email in contact_emails:
            send_notification(email, notification_type_contractor, context)
    else:
        logger.warning(
            f"Contract zone {event.contract_zone} has no contact email so cannot send "
            f'"{notification_type_contractor}" notification there.'
        )

    for official in User.objects.filter(is_official=True):
        send_notification(official.email, notification_type_official, context)
