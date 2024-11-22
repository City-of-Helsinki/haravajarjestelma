import pytest
from django.urls import reverse
from helsinki_gdpr.views import GDPRAPIView
from helusers.authz import UserAuthorization
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from areas.factories import ContractZoneFactory
from users.factories import UserFactory
from users.models import User


def _get_contract_zone_data(user: User) -> list[dict]:
    contract_zones = []

    for cz in user.contract_zones.all():
        contract_zones.append(
            {
                "key": "CONTRACTZONE",
                "children": [
                    {"key": "NAME", "value": cz.name},
                ],
            }
        )

    return contract_zones


def _get_user_data(user: User) -> list[dict]:
    return [
        {"key": "UUID", "value": user.uuid},
        {"key": "FIRST_NAME", "value": user.first_name},
        {"key": "LAST_NAME", "value": user.last_name},
        {"key": "EMAIL", "value": user.email},
        {"key": "CONTRACTZONES", "value": _get_contract_zone_data(user)},
    ]


def test_gdpr_api_get(settings):
    contract_zone = ContractZoneFactory()
    user = UserFactory()
    user.contract_zones.set([contract_zone])
    url = reverse("helsinki_gdpr:gdpr_v1", kwargs={"uuid": user.uuid})
    settings.GDPR_API_QUERY_SCOPE = "gdprquery"
    settings.OIDC_API_TOKEN_AUTH = {
        "API_AUTHORIZATION_FIELD": "authorization.permissions.scopes",
    }
    apirequest_factory = APIRequestFactory()
    request = apirequest_factory.get(url)
    user_authorization = UserAuthorization(
        user=user,
        api_token_payload={
            "authorization": {
                "permissions": {"scopes": [settings.GDPR_API_QUERY_SCOPE]}
            },
        },
    )
    force_authenticate(request, user=user, token=user_authorization)

    response = GDPRAPIView.as_view()(request, uuid=user.uuid)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"key": "USER", "children": _get_user_data(user)}


def test_gdpr_api_delete(settings):
    contract_zone = ContractZoneFactory()
    user = UserFactory()
    user.contract_zones.set([contract_zone])
    url = reverse("helsinki_gdpr:gdpr_v1", kwargs={"uuid": user.uuid})
    settings.GDPR_API_DELETE_SCOPE = "gdprdelete"
    settings.OIDC_API_TOKEN_AUTH = {
        "API_AUTHORIZATION_FIELD": "authorization.permissions.scopes",
    }
    apirequest_factory = APIRequestFactory()
    request = apirequest_factory.delete(url)
    user_authorization = UserAuthorization(
        user=user,
        api_token_payload={
            "authorization": {
                "permissions": {"scopes": [settings.GDPR_API_DELETE_SCOPE]}
            },
        },
    )
    force_authenticate(request, user=user, token=user_authorization)

    response = GDPRAPIView.as_view()(request, uuid=user.uuid)

    # Expect deletion request to be successful.
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Check that the user instance is deleted.
    with pytest.raises(user.DoesNotExist):
        user.refresh_from_db()

    # Check that the contract zone is not deleted.
    contract_zone.refresh_from_db()
