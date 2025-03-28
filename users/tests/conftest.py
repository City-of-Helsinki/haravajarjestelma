import pytest
from rest_framework.test import APIClient

from areas.factories import ContractZoneFactory
from common.tests.conftest import *  # noqa
from users.factories import UserFactory


@pytest.fixture
def user():
    """A regular user."""
    return UserFactory()


@pytest.fixture
def contractor():
    """A regular user that belongs to a contract zone."""
    user = UserFactory()
    contract_zone = ContractZoneFactory()
    contract_zone.contractor_users.add(user)
    return user


@pytest.fixture
def official():
    return UserFactory(is_official=True)


@pytest.fixture
def superuser():
    return UserFactory(is_superuser=True)


@pytest.fixture
def user_api_client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    api_client.user = user
    return api_client


@pytest.fixture
def contractor_api_client(contractor):
    api_client = APIClient()
    api_client.force_authenticate(user=contractor)
    api_client.user = contractor
    return api_client


@pytest.fixture
def official_api_client(official):
    api_client = APIClient()
    api_client.force_authenticate(user=official)
    api_client.user = official
    return api_client


@pytest.fixture
def superuser_api_client(superuser):
    api_client = APIClient()
    api_client.force_authenticate(user=superuser)
    api_client.user = superuser
    return api_client
