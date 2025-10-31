from django.contrib import admin
from django.contrib.admin import register, TabularInline
from django.contrib.auth import get_user_model
from django.contrib.gis.admin import OSMGeoAdmin
from django.utils.translation import gettext_lazy as _

from .models import ContractZone, BlockedDate

User = get_user_model()


class BlockedDateInline(TabularInline):
    """
    Inline admin for managing blocked dates directly on the ContractZone admin page.
    Shows blocked dates in a tabular format with audit information.
    """
    model = BlockedDate
    extra = 0
    fields = ("date", "reason", "created_by", "created_at")
    ordering = ("date",)
    readonly_fields = ("created_by", "created_at")

    def get_queryset(self, request):
        self.request = request  # Store request for use in formfield_for_dbfield
        return super().get_queryset(request).select_related("created_by")


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
        "name",
        "origin_id",
    )
    inlines = (BlockedDateInline,)

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

    def save_formset(self, request, form, formset, change):
        """
        Custom formset saving to handle BlockedDate inline creation.

        When creating BlockedDate instances through the inline interface,
        we need to manually set the created_by field since readonly fields
        aren't submitted in the form data.
        """
        # Check if this formset is for BlockedDate inline
        if formset.model == BlockedDate:
            # Get instances without committing to database yet
            instances = formset.save(commit=False)

            # Set created_by for new BlockedDate instances
            for instance in instances:
                if not instance.pk:  # This is a new instance (no primary key yet)
                    # Set the creator to the current admin user for audit trail
                    instance.created_by = request.user
                instance.save()

            # Save many-to-many relationships if any
            formset.save_m2m()
        else:
            # For other inlines, use default behavior
            super().save_formset(request, form, formset, change)


@register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    """
    Admin interface for managing blocked dates across all contract zones.
    Provides full CRUD operations with audit trail tracking.
    """
    list_display = ("date", "contract_zone", "reason", "created_by", "created_at")
    list_filter = ("contract_zone", "date", "created_by")
    search_fields = ("contract_zone__name", "reason")
    ordering = ("date", "contract_zone")
    readonly_fields = ("created_by", "created_at")

    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
