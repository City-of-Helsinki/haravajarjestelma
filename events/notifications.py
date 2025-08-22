import logging
from enum import Enum

from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_ilmoitin.registry import notifications
from django_ilmoitin.utils import send_notification

User = get_user_model()

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    EVENT_CREATED = ("event_created", _("Event created"))
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

    def __init__(self, value, label) -> None:
        self._value_ = value
        self.label = label


notifications.register(
    NotificationType.EVENT_CREATED.value, NotificationType.EVENT_CREATED.label
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


def send_event_created_notification(event):
    _send_notifications_to_contractor_and_officials(
        event, NotificationType.EVENT_CREATED.value
    )


def send_event_approved_notification(event):
    send_notification(
        event.organizer_email,
        NotificationType.EVENT_APPROVED_TO_ORGANIZER.value,
        {"event": event},
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
            'Contract zone {} has no contact email so cannot send "event_reminder"'
            " notification there.".format(event.contract_zone)
        )
        return

    for email in contact_emails:
        send_notification(
            email, NotificationType.EVENT_REMINDER.value, {"event": event}
        )

    event.reminder_sent_at = now()
    event.save(update_fields=("reminder_sent_at",))


def _send_notifications_to_contractor_and_officials(
    event, notification_type_contractor, notification_type_official=None
):
    if not notification_type_official:
        notification_type_official = notification_type_contractor

    contact_emails = event.contract_zone.get_contact_emails()
    if contact_emails:
        for email in contact_emails:
            send_notification(email, notification_type_contractor, {"event": event})
    else:
        logger.warning(
            'Contract zone {} has no contact email so cannot send "{}" notification'
            " there.".format(event.contract_zone, notification_type_contractor)
        )

    for official in User.objects.filter(is_official=True):
        send_notification(official.email, notification_type_official, {"event": event})
