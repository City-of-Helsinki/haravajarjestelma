import pytest
from django.contrib.auth.models import AnonymousUser

from events.permissions import (
    AllowPost,
    AllowStatePatchOnly,
    IsOfficial,
    IsSuperUser,
    ReadOnly,
)
from users.factories import UserFactory


@pytest.mark.parametrize(
    "method,expected",
    [
        ("get", True),
        ("head", True),
        ("options", True),
        ("post", False),
        ("put", False),
        ("delete", False),
        ("patch", False),
    ],
)
def test_read_only_permission(rf, method, expected):
    request = getattr(rf, method)("/foo")
    assert ReadOnly().has_permission(request, None) is expected


@pytest.mark.parametrize(
    "method,expected",
    [
        ("post", True),
        ("get", False),
        ("head", False),
        ("options", False),
        ("put", False),
        ("delete", False),
        ("patch", False),
    ],
)
def test_allow_post_permission(rf, method, expected):
    request = getattr(rf, method)("/foo")
    assert AllowPost().has_permission(request, None) is expected


@pytest.mark.parametrize(
    "method,method_expected",
    [
        ("patch", True),
        ("post", False),
        ("get", False),
        ("head", False),
        ("options", False),
        ("put", False),
        ("delete", False),
    ],
)
@pytest.mark.parametrize(
    "data,data_expected",
    [
        ({}, True),
        ({"state": 0}, True),
        ({"name": "foo"}, False),
        ({"state": 0, "name": "foo"}, False),
    ],
)
def test_allow_state_patch_only_permission(
    rf, method, data, method_expected, data_expected
):
    expected = method_expected and data_expected
    request = getattr(rf, method)("/foo", data, content_type="application/json")
    request.data = data
    assert AllowStatePatchOnly().has_permission(request, None) is expected


class IsSuperUserTest:
    def test_anonymous_user_returns_false(self, rf):
        request = rf.get("/foo")
        request.user = AnonymousUser()
        assert IsSuperUser().has_permission(request, None) is False

    def test_regular_user_returns_false(self, rf):
        request = rf.get("/foo")
        request.user = UserFactory()
        assert IsSuperUser().has_permission(request, None) is False

    def test_superuser_returns_true(self, rf):
        request = rf.get("/foo")
        request.user = UserFactory(is_superuser=True)
        assert IsSuperUser().has_permission(request, None) is True


class IsOfficialTest:
    def test_anonymous_user_returns_false(self, rf):
        request = rf.get("/foo")
        request.user = AnonymousUser()
        assert IsOfficial().has_permission(request, None) is False

    def test_regular_user_returns_false(self, rf):
        request = rf.get("/foo")
        request.user = UserFactory()
        assert IsOfficial().has_permission(request, None) is False

    def test_official_user_returns_true(self, rf):
        request = rf.get("/foo")
        request.user = UserFactory(is_official=True)
        assert IsOfficial().has_permission(request, None) is True
