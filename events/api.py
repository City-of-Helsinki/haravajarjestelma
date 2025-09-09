import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
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

        if (start_time and end_time) and (start_time > end_time):
            raise serializers.ValidationError(_("Event must start before ending."))

        now = timezone.now()
        if start_time > now + relativedelta(months=6):
            raise serializers.ValidationError(_(
                "Event cannot start later than six months from now."
            ))

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


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filterset_fields = ("contract_zone",)
    permission_classes = [
        IsSuperUser
        | IsOfficial
        | (IsAuthenticated & (AllowPut | AllowPatch))
        | AllowPost
        | ReadOnly
    ]

    def get_queryset(self):
        return self.queryset.filter_for_user(self.request.user)

    # overwrite default create to add captcha validation
    def create(self, request, *args, **kwargs):
        recaptcha_token = request.data.get("recaptchaToken")
        if not recaptcha_token:
            raise serializers.ValidationError(
                {"recaptcha": "reCAPTCHA token is required."}
            )

        data = {
            "secret": settings.RECAPTCHA_SECRET,
            "response": recaptcha_token,
        }

        try:
            response = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data=data
            )
            response.raise_for_status()
            result = response.json()
        except requests.RequestException:
            raise serializers.ValidationError(
                {"recaptcha": "Error verifying reCAPTCHA. Please try again later."}
            )

        if not result.get("success"):
            raise serializers.ValidationError(
                {"recaptcha": "Invalid reCAPTCHA. Please try again."}
            )

        return super().create(request, *args, **kwargs)
