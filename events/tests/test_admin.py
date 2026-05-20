import pytest
from django.core.exceptions import ValidationError
from django.utils import translation

from events.admin import ValidatedNotificationTemplateForm
from events.notifications import NotificationType


def call_clean(body_html="", body_text="", subject="Hello"):
    form = ValidatedNotificationTemplateForm.__new__(ValidatedNotificationTemplateForm)
    form.cleaned_data = {
        "type": NotificationType.EVENT_RECEIVED.value,
        "subject": subject,
        "body_html": body_html,
        "body_text": body_text,
    }
    with translation.override("fi"):
        return form.clean()


def test_clean_valid_template():
    call_clean(body_html="{{ event.name }}")


def test_clean_invalid_subject_raises_error():
    with pytest.raises(
        ValidationError,
        match="subject: template rendering failed: 'undefined_variable' is undefined",
    ):
        call_clean(subject="{{ undefined_variable }}")


def test_clean_invalid_body_html_raises_error():
    with pytest.raises(
        ValidationError,
        match="body_html: template rendering failed: 'undefined_variable' is undefined",
    ):
        call_clean(body_html="{{ undefined_variable }}")


def test_clean_invalid_body_text_raises_error():
    with pytest.raises(
        ValidationError,
        match="body_text: template rendering failed: 'undefined_variable' is undefined",
    ):
        call_clean(body_text="{{ undefined_variable }}")
