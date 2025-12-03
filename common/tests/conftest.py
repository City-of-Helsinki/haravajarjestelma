import factory.random
import pytest
from django.utils.translation import gettext_lazy as _
from freezegun import freeze_time
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def set_random_seed():
    factory.random.reseed_random(777)


@pytest.fixture(autouse=True)
def set_frozen_time():
    with freeze_time("2018-01-14T08:00:00Z"):
        yield


@pytest.fixture(autouse=True)
def force_settings(settings):
    settings.LANGUAGE_CODE = "en"
    settings.LANGUAGES = (("fi", _("Finnish")),)
    settings.EVENT_MINIMUM_DAYS_BEFORE_START = 6
    settings.EVENT_REMINDER_DAYS_IN_ADVANCE = 2
    settings.APPROVAL_REMINDER_DAYS_AFTER_CREATION = 3
    settings.APPROVAL_REMINDER_DAYS_BEFORE_EVENT = 5
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@foo.bar"


@pytest.fixture(autouse=True)
def autouse_django_db(db):
    pass


@pytest.fixture
def api_client():
    return APIClient()
