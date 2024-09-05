import os
import pytest
from django.contrib.gis.gdal import DataSource

from areas.importer.helsinki import HelsinkiImporter

TEST_DATA = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture
def ds_geojson_simple():
    return DataSource(f"{TEST_DATA}/geojson_simple.json")


def test_get_attribute_safe_returns_value_as_string(ds_geojson_simple):
    layer = ds_geojson_simple[0]
    feature = layer[0]
    for field in feature.fields:
        result = HelsinkiImporter._get_attribute_safe(feature, field)
        assert isinstance(result, str)


def test_get_attribute_safe_returns_empty_string_if_attribute_missing(
    ds_geojson_simple,
):
    layer = ds_geojson_simple[0]
    feature = layer[0]
    result = HelsinkiImporter._get_attribute_safe(feature, "missing_attribute")
    assert result == ""


def test_get_attribute_safe_returns_empty_string_if_none(ds_geojson_simple):
    layer = ds_geojson_simple[0]
    feature = layer[0]
    result = HelsinkiImporter._get_attribute_safe(feature, "null")
    assert result == ""
