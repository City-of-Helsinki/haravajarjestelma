import pytest
import responses
from responses import matchers

from areas.digitransit import DigitransitApiError
from common.tests.utils import get

ADDRESS_SEARCH_URL = "/v1/address_search/"

MOCK_DIGITRANSIT_ADDRESS_SEARCH_URL = "http://localhost:9999/digitransit/v1/search"
MOCK_DIGITRANSIT_API_KEY = "top-secret-test-api-key-123"

COMMON_EXPECTED_DIGITRANSIT_PARAMS = {
    "boundary.rect.min_lat": "60.1",
    "boundary.rect.max_lat": "60.3",
    "boundary.rect.min_lon": "24.73",
    "boundary.rect.max_lon": "25.33",
    "size": 5,
    "layers": "address",
}


@pytest.fixture(autouse=True)
def mocked_responses(settings):
    settings.DIGITRANSIT_ADDRESS_SEARCH_URL = MOCK_DIGITRANSIT_ADDRESS_SEARCH_URL
    settings.DIGITRANSIT_API_KEY = MOCK_DIGITRANSIT_API_KEY

    with responses.RequestsMock() as rsps:
        yield rsps


MOCK_RESPONSE = {
    "geocoding": {
        "version": "0.2",
        "attribution": "http://pelias-api:8080/attribution",
        "query": {
            "text": "lumikintie",
            "size": 5,
            "lang": "fi",
            "layers": ["address"],
            "private": False,
            "boundary.rect.min_lat": 60.1,
            "boundary.rect.max_lat": 60.3,
            "boundary.rect.min_lon": 24.73,
            "boundary.rect.max_lon": 25.33,
            "boundary.country": ["FIN"],
            "querySize": 50,
            "parsed_text": {"name": "lumikintie"},
        },
        "engine": {"name": "Pelias", "author": "Mapzen", "version": "1.0"},
        "timestamp": 1715029813550,
    },
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.057749, 60.202563]},
            "properties": {
                "id": "way:16085704",
                "gid": "openstreetmap:address:way:16085704",
                "layer": "address",
                "source": "openstreetmap",
                "source_id": "way:16085704",
                "name": "Lumikintie 4",
                "housenumber": "4",
                "street": "Lumikintie",
                "postalcode": "00820",
                "postalcode_gid": "whosonfirst:postalcode:421473125",
                "confidence": 0.9983471074380166,
                "accuracy": "point",
                "region": "Uusimaa",
                "region_gid": "whosonfirst:region:85683067",
                "localadmin": "Helsinki",
                "localadmin_gid": "whosonfirst:localadmin:907199715",
                "locality": "Helsinki",
                "locality_gid": "whosonfirst:locality:101748417",
                "neighbourhood": "Roihuvuori",
                "neighbourhood_gid": "whosonfirst:neighbourhood:1108727173",
                "label": "Lumikintie 4, Helsinki",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.054729, 60.204275]},
            "properties": {
                "id": "way:16085893",
                "gid": "openstreetmap:address:way:16085893",
                "layer": "address",
                "source": "openstreetmap",
                "source_id": "way:16085893",
                "name": "Lumikintie 5",
                "housenumber": "5",
                "street": "Lumikintie",
                "postalcode": "00820",
                "postalcode_gid": "whosonfirst:postalcode:421473125",
                "confidence": 0.9983471074380166,
                "accuracy": "point",
                "region": "Uusimaa",
                "region_gid": "whosonfirst:region:85683067",
                "localadmin": "Helsinki",
                "localadmin_gid": "whosonfirst:localadmin:907199715",
                "locality": "Helsinki",
                "locality_gid": "whosonfirst:locality:101748417",
                "neighbourhood": "Roihuvuori",
                "neighbourhood_gid": "whosonfirst:neighbourhood:1108727173",
                "label": "Lumikintie 5, Helsinki",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.055386, 60.202539]},
            "properties": {
                "id": "way:16085806",
                "gid": "openstreetmap:address:way:16085806",
                "layer": "address",
                "source": "openstreetmap",
                "source_id": "way:16085806",
                "name": "Lumikintie 6",
                "housenumber": "6",
                "street": "Lumikintie",
                "postalcode": "00820",
                "postalcode_gid": "whosonfirst:postalcode:421473125",
                "confidence": 0.9983471074380166,
                "accuracy": "point",
                "region": "Uusimaa",
                "region_gid": "whosonfirst:region:85683067",
                "localadmin": "Helsinki",
                "localadmin_gid": "whosonfirst:localadmin:907199715",
                "locality": "Helsinki",
                "locality_gid": "whosonfirst:locality:101748417",
                "neighbourhood": "Roihuvuori",
                "neighbourhood_gid": "whosonfirst:neighbourhood:1108727173",
                "label": "Lumikintie 6, Helsinki",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.05391, 60.20345]},
            "properties": {
                "id": "way:16085874",
                "gid": "openstreetmap:address:way:16085874",
                "layer": "address",
                "source": "openstreetmap",
                "source_id": "way:16085874",
                "name": "Lumikintie 7",
                "housenumber": "7",
                "street": "Lumikintie",
                "postalcode": "00820",
                "postalcode_gid": "whosonfirst:postalcode:421473125",
                "confidence": 0.9983471074380166,
                "accuracy": "point",
                "region": "Uusimaa",
                "region_gid": "whosonfirst:region:85683067",
                "localadmin": "Helsinki",
                "localadmin_gid": "whosonfirst:localadmin:907199715",
                "locality": "Helsinki",
                "locality_gid": "whosonfirst:locality:101748417",
                "neighbourhood": "Roihuvuori",
                "neighbourhood_gid": "whosonfirst:neighbourhood:1108727173",
                "label": "Lumikintie 7, Helsinki",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.058641, 60.203472]},
            "properties": {
                "id": "way:16085980",
                "gid": "openstreetmap:address:way:16085980",
                "layer": "address",
                "source": "openstreetmap",
                "source_id": "way:16085980",
                "name": "Lumikintie 1",
                "housenumber": "1",
                "street": "Lumikintie",
                "postalcode": "00820",
                "postalcode_gid": "whosonfirst:postalcode:421473125",
                "confidence": 0.9983471074380166,
                "accuracy": "point",
                "region": "Uusimaa",
                "region_gid": "whosonfirst:region:85683067",
                "localadmin": "Helsinki",
                "localadmin_gid": "whosonfirst:localadmin:907199715",
                "locality": "Helsinki",
                "locality_gid": "whosonfirst:locality:101748417",
                "neighbourhood": "Roihuvuori",
                "neighbourhood_gid": "whosonfirst:neighbourhood:1108727173",
                "label": "Lumikintie 1, Helsinki",
            },
        },
    ],
    "bbox": [25.05391, 60.202539, 25.058641, 60.204275],
}


expected_response = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.057749, 60.202563]},
            "properties": {
                "name": "Lumikintie 4",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.054729, 60.204275]},
            "properties": {
                "name": "Lumikintie 5",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.055386, 60.202539]},
            "properties": {
                "name": "Lumikintie 6",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.05391, 60.20345]},
            "properties": {
                "name": "Lumikintie 7",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [25.058641, 60.203472]},
            "properties": {
                "name": "Lumikintie 1",
            },
        },
    ],
}


@pytest.mark.parametrize(
    "query_string, expected_digitransit_params",
    [
        ("text=lumikintie&language=fi", {"text": "lumikintie", "lang": "fi"}),
        (
            "text=snövits väg&language=sv",
            {"text": "snövits väg", "lang": "sv"},
        ),
        ("text=lumikintie", {"text": "lumikintie", "lang": "fi"}),
    ],
)
def test_address_search_returns_correct_response_when_digitransit_request_successful(
    api_client, mocked_responses, query_string, expected_digitransit_params
):
    mocked_responses.get(
        MOCK_DIGITRANSIT_ADDRESS_SEARCH_URL,
        match=[
            matchers.query_param_matcher(
                COMMON_EXPECTED_DIGITRANSIT_PARAMS | expected_digitransit_params
            ),
            matchers.header_matcher(
                {"digitransit-subscription-key": MOCK_DIGITRANSIT_API_KEY}
            ),
        ],
        json=MOCK_RESPONSE,
        status=200,
    )

    response = get(api_client, f"{ADDRESS_SEARCH_URL}?{query_string}")
    assert response == expected_response


def test_address_search_returns_error_when_digitransit_responds_http_error(
    api_client, mocked_responses
):
    mocked_responses.get(
        MOCK_DIGITRANSIT_ADDRESS_SEARCH_URL,
        json={"error": "some-unknown-error"},
        status=503,
    )

    with pytest.raises(DigitransitApiError):
        get(api_client, ADDRESS_SEARCH_URL + "?text=lumikintie&language=fi")


def test_address_search_returns_error_when_digitransit_responds_invalid_json(
    api_client, mocked_responses
):
    mocked_responses.get(
        MOCK_DIGITRANSIT_ADDRESS_SEARCH_URL,
        body="no-json",
        status=200,
    )

    with pytest.raises(DigitransitApiError) as e:
        get(api_client, ADDRESS_SEARCH_URL + "?text=lumikintie&language=fi")
    assert "JSONDecodeError" in str(e)


def test_address_search_returns_error_when_digitransit_responds_improper_json(
    api_client, mocked_responses
):
    mocked_responses.get(
        MOCK_DIGITRANSIT_ADDRESS_SEARCH_URL,
        json={"foo": "bar"},
        status=200,
    )

    with pytest.raises(DigitransitApiError) as e:
        get(api_client, ADDRESS_SEARCH_URL + "?text=lumikintie&language=fi")
    assert "KeyError" in str(e)
