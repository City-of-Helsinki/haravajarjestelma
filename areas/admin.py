from django.contrib.admin import register
from django.contrib.auth import get_user_model
from django.contrib.gis.admin import OSMGeoAdmin
from django.utils.translation import gettext_lazy as _

from .models import ContractZone

User = get_user_model()


@register(ContractZone)
class ContractZoneAdmin(OSMGeoAdmin):
    default_lon = 2776460  # Central Railway Station in EPSG:3857
    default_lat = 8438120
    default_zoom = 10
    modifiable = False
    list_display = (
        "name",
        "contractor",
        "contact_person",
        "email",
        "secondary_contact_person",
        "secondary_email",
        "active",
    )
    ordering = ("name",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "boundary",
                    "active",
                    "origin_id",
                    "contractor",
                    ("contact_person", "phone", "email"),
                    ("secondary_contact_person", "secondary_phone", "secondary_email"),
                )
            },
        ),
        (_("Users"), {"fields": ("contractor_users",)}),
    )
    readonly_fields = (
        "active",
        "name",
        "origin_id",
        "contractor",
        "contact_person",
        "phone",
        "email",
        "secondary_contact_person",
        "secondary_phone",
        "secondary_email",
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "contractor_users":
            field.queryset = User.objects.order_by("email")
        return field

    def has_add_permission(self, request, obj=None):
        return False

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["contractor_users"].widget.can_add_related = False
        return form
