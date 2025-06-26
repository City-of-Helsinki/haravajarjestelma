from django.contrib.admin import TabularInline, register
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ContractZoneInline(TabularInline):
    model = User.contract_zones.through
    extra = 0


@register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = (ContractZoneInline,)
    fieldsets = DjangoUserAdmin.fieldsets + (
        (_("AD groups"), {"fields": ("ad_groups",)}),
        (_("Roles"), {"fields": ("is_official",)}),
    )
