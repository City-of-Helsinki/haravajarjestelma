from django import forms
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.translation import gettext_lazy as _
from django_ilmoitin.admin import NotificationTemplateAdmin, NotificationTemplateForm
from django_ilmoitin.models import NotificationTemplate
from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

from .dummy_context import dummy_context
from .models import Event


class ValidatedNotificationTemplateForm(NotificationTemplateForm):
    def clean(self):
        cleaned_data = super().clean()
        template_type = cleaned_data.get("type")
        if not template_type:
            return cleaned_data

        context = dummy_context.get(template_type)
        env = SandboxedEnvironment(
            trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined
        )
        for field in "subject", "body_html", "body_text":
            value = cleaned_data.get(field) or ""
            try:
                env.from_string(value).render(context)
            except Exception as e:
                raise forms.ValidationError(
                    _("%(field)s: template rendering failed: %(error)s"),
                    params={"field": field, "error": str(e)},
                ) from e

        return cleaned_data


class ValidatedNotificationTemplateAdmin(NotificationTemplateAdmin):
    form = ValidatedNotificationTemplateForm


admin.site.unregister(NotificationTemplate)
admin.site.register(NotificationTemplate, ValidatedNotificationTemplateAdmin)


@admin.register(Event)
class EventAdmin(GISModelAdmin):
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": 10,
            "default_lon": 24.941389,  # Central Railway Station in EPSG:4326,
            "default_lat": 60.171944,
        },
    }
    list_display = (
        "name",
        "start_time",
        "end_time",
        "contract_zone",
        "state",
        "created_at",
        "modified_at",
    )
    readonly_fields = ("contract_zone",)
