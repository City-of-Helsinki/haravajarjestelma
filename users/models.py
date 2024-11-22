from django.db import models
from django.utils.translation import gettext_lazy as _
from helsinki_gdpr.models import SerializableMixin
from helusers.models import AbstractUser


class User(AbstractUser, SerializableMixin):
    serialize_fields = (
        {"name": "uuid"},
        {"name": "first_name"},
        {"name": "last_name"},
        {"name": "email"},
        {"name": "contractzones"},
    )

    is_official = models.BooleanField(verbose_name=_("official"), default=False)

    @property
    def contractzones(self):
        """
        SerializableMixin doesn't fully support many-to-many fields, so we need to
        serialize the contract zones separately.
        """
        return [cz.serialize() for cz in self.contract_zones.all()]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("id",)


def can_view_contract_zone_details(user):
    return user.is_authenticated and user.is_official
