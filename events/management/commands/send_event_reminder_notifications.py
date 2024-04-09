import logging
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import localtime, now

from common.utils import get_today, is_vacation_day, ONE_DAY
from events.models import Event
from events.notifications import send_event_reminder_notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send event reminder notifications to contractors"

    def handle(self, *args, **options):
        logger.info("Sending event reminder notifications (if needed)")
        today = get_today()

        for event in Event.objects.filter(start_time__gt=now(), reminder_sent_at=None):
            reminder_day = localtime(event.start_time).date() - timedelta(
                days=settings.EVENT_REMINDER_DAYS_IN_ADVANCE
            )
            while is_vacation_day(reminder_day):
                reminder_day -= ONE_DAY

            if today == reminder_day:
                send_event_reminder_notification(event)
