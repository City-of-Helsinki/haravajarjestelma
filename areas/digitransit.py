from typing import Literal

import requests
from django.conf import settings

DIGITRANSIT_API_KEY_HEADER = "digitransit-subscription-key"

BOUNDARY_MIN_LAT = "60.1"
BOUNDARY_MAX_LAT = "60.3"
BOUNDARY_MIN_LON = "24.73"
BOUNDARY_MAX_LON = "25.33"
NUM_OF_RESULTS = 5
REQUEST_TIMEOUT = 10  # secs


class DigitransitApiError(Exception):
    pass


def digitransit_address_search(
    text: str, language: Literal["fi", "sv", "en"] = "fi"
) -> dict:
    try:
        digitransit_response = requests.get(
            settings.DIGITRANSIT_ADDRESS_SEARCH_URL,
            params={
                "text": text,
                "lang": language,
                "boundary.rect.min_lat": BOUNDARY_MIN_LAT,
                "boundary.rect.max_lat": BOUNDARY_MAX_LAT,
                "boundary.rect.min_lon": BOUNDARY_MIN_LON,
                "boundary.rect.max_lon": BOUNDARY_MAX_LON,
                "size": NUM_OF_RESULTS,
                "layers": "address",
            },
            headers={"digitransit-subscription-key": settings.DIGITRANSIT_API_KEY},
            timeout=REQUEST_TIMEOUT,
        )
        digitransit_response.raise_for_status()
        digitransit_response_json = digitransit_response.json()

        response = {
            "type": digitransit_response_json["type"],
            "features": [
                {
                    "type": feature["type"],
                    "geometry": feature["geometry"],
                    "properties": {
                        "name": feature["properties"]["name"],
                    },
                }
                for feature in digitransit_response_json["features"]
            ],
        }
    except (requests.exceptions.RequestException, KeyError) as e:
        raise DigitransitApiError("Digitransit API request failed:", e) from e

    return response
