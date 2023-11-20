from django.db import models
from django.utils.translation import gettext_lazy as _
from helusers.models import AbstractUser


class User(AbstractUser):
    is_official = models.BooleanField(verbose_name=_("official"), default=False)

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("id",)


def can_view_contract_zone_details(user):
    return user.is_authenticated and user.is_official
