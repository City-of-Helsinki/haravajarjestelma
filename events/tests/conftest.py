import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon

from areas.factories import ContractZoneFactory
from common.tests.conftest import *  # noqa
from users.tests.conftest import *  # noqa

from ..factories import EventFactory


@pytest.fixture
def event():
    return EventFactory()


@pytest.fixture
def event_with_contract_zone():
    contract_zone = ContractZoneFactory(boundary=MultiPolygon(
        Polygon((
            (24, 60),
            (25, 60),
            (25, 61),
            (24, 61),
            (24, 60),
        ))
    ))
    event = EventFactory(location=Point(24.5, 60.5))
    assert event.contract_zone == contract_zone
    return event
