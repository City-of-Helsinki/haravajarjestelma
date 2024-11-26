import pytest

from areas.factories import ContractZoneFactory
from common.tests.conftest import *  # noqa
from users.tests.conftest import *  # noqa

from ..factories import EventFactory


@pytest.fixture
def contract_zone():
    return ContractZoneFactory()


@pytest.fixture
def event():
    return EventFactory()
