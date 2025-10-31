import pytest

from common.tests.utils import get
from users.factories import UserFactory

BASE_URL = "/v1/user/"


def test_list_url_not_available(user_api_client):
    get(user_api_client, BASE_URL, status_code=404)


@pytest.mark.parametrize("lookup", ["uuid", "me"])
def test_unauthenticated_user_cannot_get(api_client, user, lookup):
    if lookup == "uuid":
        lookup = user.uuid  # this is some other user

    get(api_client, f"{BASE_URL}{lookup}/", status_code=404)


def test_cannot_get_other_user(user_api_client):
    user = UserFactory()

    get(user_api_client, f"{BASE_URL}{user.uuid}/", status_code=404)


@pytest.mark.parametrize("lookup", ["uuid", "me"])
def test_user_get(user_api_client, lookup):
    user = user_api_client.user
    if lookup == "uuid":
        lookup = user.uuid

    response_data = get(user_api_client, f"{BASE_URL}{lookup}/")

    assert response_data == {
        "uuid": str(user.uuid),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_official": False,
        "is_contractor": False,
    }


@pytest.mark.parametrize("is_contractor", (True, False))
def test_user_get_is_contractor(user_api_client, contractor_api_client, is_contractor):
    api_client = contractor_api_client if is_contractor else user_api_client
    response_data = get(api_client, BASE_URL + "me/")
    assert response_data["is_contractor"] is is_contractor
