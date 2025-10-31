from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Event


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
