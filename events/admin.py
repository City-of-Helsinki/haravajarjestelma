from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models import Event


@admin.register(Event)
class EventAdmin(OSMGeoAdmin):
    default_lon = 2776460  # Central Railway Station in EPSG:3857
    default_lat = 8438120
    default_zoom = 10
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
