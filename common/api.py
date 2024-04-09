import pytz
from copy import deepcopy
from django.db import models
from rest_framework import serializers


class UTCDateTimeField(serializers.DateTimeField):
    def __init__(self, *args, **kwargs):
        kwargs.update(default_timezone=pytz.UTC)
        super().__init__(*args, **kwargs)


class UTCModelSerializer(serializers.ModelSerializer):
    serializer_field_mapping = deepcopy(
        serializers.ModelSerializer.serializer_field_mapping
    )
    serializer_field_mapping[models.DateTimeField] = UTCDateTimeField
