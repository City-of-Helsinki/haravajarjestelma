from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from areas.models import ContractZone
from common.api import UTCModelSerializer
from common.utils import date_range
from events.models import ERROR_MSG_NO_CONTRACT_ZONE, Event
from events.permissions import (
    AllowPatch,
    AllowPost,
    AllowPut,
    IsOfficial,
    IsSuperUser,
    ReadOnly,
)


class PublicEventSerializer(UTCModelSerializer):
    class Meta:
        model = Event
        fields = ("name", "start_time", "end_time", "location")


class EventSerializer(UTCModelSerializer):
    class Meta:
        model = Event
        exclude = ("reminder_sent_at",)
        read_only_fields = ("contract_zone",)

    def get_fields(self):
        fields = super().get_fields()
        if not self.instance:
            fields["state"].read_only = True
        return fields

    def validate(self, data):
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        # PATCH updates only 'state', so check that start and end times are present in
        # the data
        if start_time and end_time:
            if start_time > end_time:
                raise serializers.ValidationError(_("Event must start before ending."))

        if start_time:
            now = timezone.now()
            if start_time > now + timedelta(
                days=settings.EVENT_MAXIMUM_DAYS_TO_START
            ):
                raise serializers.ValidationError(
                    _("Event cannot start later than {days} days from now.").format(
                        days=settings.EVENT_MAXIMUM_DAYS_TO_START
                    )
                )

        max_duration = timedelta(settings.EVENT_MAXIMUM_DAYS_LENGTH)
        if start_time and end_time and (end_time - start_time) > max_duration:
            raise serializers.ValidationError(
                _("The event duration cannot exceed {days} days.").format(
                    days=settings.EVENT_MAXIMUM_DAYS_LENGTH
                )
            )

        location = data.get("location")
        if location:
            data["contract_zone"] = ContractZone.objects.get_active_by_location(
                location
            )
            if not data["contract_zone"]:
                raise serializers.ValidationError(
                    {"location": ERROR_MSG_NO_CONTRACT_ZONE}
                )

            if start_time or end_time:
                start_date = localtime(start_time or self.instance.start_time).date()
                end_date = localtime(end_time or self.instance.end_time).date()
                zone_unavailable_dates = data["contract_zone"].get_unavailable_dates(
                    exclude_event=self.instance
                )
                unavailable_dates = set(date_range(start_date, end_date)) & set(
                    zone_unavailable_dates
                )
                if unavailable_dates:
                    raise serializers.ValidationError(
                        _("Unavailable dates: {}".format(sorted(unavailable_dates)))
                    )

        return data


class EventFilter(filters.FilterSet):
    start_time_gte = filters.DateTimeFilter(field_name="start_time", lookup_expr="gte")
    start_time_lte = filters.DateTimeFilter(field_name="start_time", lookup_expr="lte")
    end_time_gte = filters.DateTimeFilter(field_name="end_time", lookup_expr="gte")
    end_time_lte = filters.DateTimeFilter(field_name="end_time", lookup_expr="lte")

    class Meta:
        model = Event
        fields = [
            "contract_zone",
            "state",
            "start_time_gte",
            "start_time_lte",
            "end_time_gte",
            "end_time_lte",
        ]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filterset_class = EventFilter
    permission_classes = [
        IsSuperUser
        | IsOfficial
        | (IsAuthenticated & (AllowPut | AllowPatch))
        | AllowPost
        | ReadOnly
    ]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update") or (
            self.request.user and self.request.user.is_authenticated
        ):
            return EventSerializer
        return PublicEventSerializer

    def get_queryset(self):
        # Allow unauthenticated users to see only approved events
        if not self.request.user.is_authenticated:
            return self.queryset.filter(state=Event.APPROVED)
        return self.queryset.filter_for_user(self.request.user)
