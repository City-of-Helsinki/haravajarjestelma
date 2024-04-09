import holidays
from datetime import timedelta
from django.core import mail
from django.utils.timezone import localtime, now

ONE_DAY = timedelta(days=1)
SATURDAY = 6
SUNDAY = 7
HOLIDAYS_FINLAND = holidays.Finland()


def get_today():
    return localtime(now()).date()


def date_range(start, end):
    current = start
    while current <= end:
        yield current
        current += ONE_DAY


def is_vacation_day(date):
    return date.isoweekday() in (SATURDAY, SUNDAY) or date in HOLIDAYS_FINLAND


def assert_to_addresses(*expected_to_addresses, mails=None):
    if mails is None:
        mails = mail.outbox
    to_addresses = set((m.to[0] for m in mails))
    expected_to_addresses = set(expected_to_addresses)
    assert (
        to_addresses == expected_to_addresses
    ), f"{to_addresses} does not match {expected_to_addresses}"
