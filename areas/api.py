from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Count, Q, Sum
from django_filters import rest_framework as filters
from munigeo.models import Address, Street
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from areas.digitransit import digitransit_address_search
from areas.models import ContractZone
from common.api import UTCModelSerializer
from events.models import Event
from users.models import can_view_contract_zone_details


class TranslatedModelSerializer(TranslatableModelSerializer, UTCModelSerializer):
    translations = TranslatedFieldsField()

    def to_representation(self, obj):
        ret = super(TranslatedModelSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        return self.translated_fields_to_representation(obj, ret)

    def translated_fields_to_representation(self, obj, ret):
        translated_fields = {}

        for lang_key, trans_dict in ret.pop("translations", {}).items():
            for field_name, translation in trans_dict.items():
                if field_name not in translated_fields:
                    translated_fields[field_name] = {lang_key: translation}
                else:
                    translated_fields[field_name].update({lang_key: translation})

        ret.update(translated_fields)

        return ret


class GeoQueryParamSerializer(serializers.Serializer):
    lat = serializers.FloatField(required=True)
    lon = serializers.FloatField(required=True)


class StreetSerializer(TranslatedModelSerializer):
    class Meta:
        model = Street
        fields = ("name", "translations")


class AddressSerializer(UTCModelSerializer):
    street = StreetSerializer()
    distance = serializers.FloatField(source="distance.m")

    class Meta:
        model = Address
        exclude = ("id", "modified_at")


class ContractZoneSerializerBase(UTCModelSerializer):
    class Meta:
        model = ContractZone
        fields = ("id", "name", "active")


class ContractZoneSerializerGeoQueryView(ContractZoneSerializerBase):
    unavailable_dates = serializers.ReadOnlyField(source="get_unavailable_dates")

    class Meta(ContractZoneSerializerBase.Meta):
        fields = ContractZoneSerializerBase.Meta.fields + ("unavailable_dates",)


class GeoQueryViewSet(viewsets.ViewSet):
    def list(self, request, format=None):
        param_serializer = GeoQueryParamSerializer(data=request.query_params)
        param_serializer.is_valid(raise_exception=True)

        point = Point(
            param_serializer.validated_data["lon"],
            param_serializer.validated_data["lat"],
            srid=settings.DEFAULT_SRID,
        )
        address = self.get_closest_address(point)
        contract_zone = ContractZone.objects.get_active_by_location(point)

        data = {
            "closest_address": AddressSerializer(address).data if address else None,
            "contract_zone": (
                ContractZoneSerializerGeoQueryView(contract_zone).data
                if contract_zone
                else None
            ),
        }

        return Response(data)

    @classmethod
    def get_closest_address(cls, point):
        return (
            Address.objects.annotate(distance=Distance("location", point))
            .order_by("distance")
            .first()
        )


class ContractZoneSerializer(ContractZoneSerializerBase):
    def to_representation(self, instance):
        data = super().to_representation(instance)

        if "request" in self.context and can_view_contract_zone_details(
            self.context["request"].user
        ):
            data.update(
                contact_person=self._get_contact_person_display(instance),
                email=self._get_email_display(instance),
                phone=instance.phone,
            )
            if hasattr(instance, "event_count") and hasattr(
                instance, "estimated_attendee_count"
            ):
                data.update(
                    event_count=instance.event_count or 0,
                    estimated_attendee_count=instance.estimated_attendee_count or 0,
                )

        return data

    @classmethod
    def _get_contact_person_display(cls, contract_zone):
        return contract_zone.contact_person or ""

    @classmethod
    def _get_email_display(cls, contract_zone):
        return contract_zone.email or ""


class ContractZoneFilter(filters.FilterSet):
    stats_year = filters.NumberFilter(method="filter_stats")

    def filter_stats(self, queryset, name, value):
        if can_view_contract_zone_details(self.request.user):
            filtering = Q(
                events__start_time__date__year=value, events__state=Event.APPROVED
            )
            queryset = queryset.order_by("id").annotate(
                event_count=Count("events", filter=filtering),
                estimated_attendee_count=Sum(
                    "events__estimated_attendee_count", filter=filtering
                ),
            )

        return queryset


class ContractZoneViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContractZone.objects.all()
    serializer_class = ContractZoneSerializer
    filterset_class = ContractZoneFilter


class AddressSearchParamSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)
    language = serializers.ChoiceField(choices=["fi", "sv", "en"], default="fi")


class AddressSearchViewSet(viewsets.ViewSet):
    def list(self, request, format=None):
        param_serializer = AddressSearchParamSerializer(data=request.query_params)
        param_serializer.is_valid(raise_exception=True)

        text = param_serializer.data["text"]
        language = param_serializer.data["language"]
        data = digitransit_address_search(text, language)

        return Response(data)
