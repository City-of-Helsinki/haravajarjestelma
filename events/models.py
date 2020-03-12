from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from areas.models import ContractZone
from events.signals import event_approved

ERROR_MSG_NO_CONTRACT_ZONE = _("Location must be inside a contract zone.")


class EventQuerySet(models.QuerySet):
    def filter_for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        elif user.is_superuser or user.is_official:
            return self
        else:
            return self.filter(contract_zone__contractor_users=user)


class Event(models.Model):
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    APPROVED = "approved"
    STATES = (
        (WAITING_FOR_APPROVAL, _("waiting for approval")),
        (APPROVED, _("approved")),
    )

    state = models.CharField(
        verbose_name=_("state"),
        max_length=50,
        choices=STATES,
        default=WAITING_FOR_APPROVAL,
    )
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_("modified at"), auto_now=True)

    name = models.CharField(verbose_name=_("name"), max_length=255)
    description = models.TextField(verbose_name=_("description"), blank=True)
    start_time = models.DateTimeField(verbose_name=_("start time"))
    end_time = models.DateTimeField(verbose_name=_("end time"))
    location = models.PointField(verbose_name=_("location"), srid=settings.DEFAULT_SRID)

    organizer_first_name = models.CharField(
        verbose_name=_("organizer first name"), max_length=100
    )
    organizer_last_name = models.CharField(
        verbose_name=_("organizer last name"), max_length=100
    )
    organizer_email = models.EmailField(verbose_name=_("organizer email"))
    organizer_phone = models.CharField(verbose_name=_("organizer phone"), max_length=50)

    estimated_attendee_count = models.PositiveIntegerField(
        verbose_name=_("estimated attendee count")
    )
    targets = models.TextField(verbose_name=_("targets"))
    maintenance_location = models.TextField(verbose_name=_("maintenance location"))
    additional_information = models.TextField(
        verbose_name=_("additional information"), blank=True
    )

    small_trash_bag_count = models.PositiveIntegerField(
        verbose_name=_("small trash bag count")
    )
    large_trash_bag_count = models.PositiveIntegerField(
        verbose_name=_("large trash bag count")
    )
    trash_picker_count = models.PositiveIntegerField(
        verbose_name=_("trash picker count")
    )
    equipment_information = models.TextField(
        verbose_name=_("additional equipment information"), blank=True
    )

    contract_zone = models.ForeignKey(
        ContractZone,
        verbose_name=_("contract zone"),
        related_name="events",
        on_delete=models.PROTECT,
    )

    reminder_sent_at = models.DateTimeField(
        verbose_name=_("reminder notification sent at"),
        blank=True,
        null=True,
        editable=False,
    )

    objects = EventQuerySet.as_manager()

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ("id",)

    def __str__(self):
        return self.name

    def clean(self):
        contract_zone = ContractZone.objects.get_by_location(self.location)
        if not contract_zone:
            raise ValidationError(
                {"location": ERROR_MSG_NO_CONTRACT_ZONE}, code="no_contract_zone"
            )
        self.contract_zone = contract_zone

    def save(self, *args, **kwargs):
        if self.pk:
            # this is not optimal as it causes an extra hit to the db, but event modifications are so
            # infrequent that we don't bother to build more complex logic for this
            old_state = Event.objects.get(pk=self.pk).state

            super().save(*args, **kwargs)
            if old_state == Event.WAITING_FOR_APPROVAL and self.state == Event.APPROVED:
                event_approved.send(self.__class__, instance=self)
        else:
            super().save(*args, **kwargs)
