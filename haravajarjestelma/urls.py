from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from areas.api import AddressSearchViewSet, ContractZoneViewSet, GeoQueryViewSet
from events.api import EventViewSet
from users.api import UserViewSet

router = DefaultRouter()
router.register("event", EventViewSet)
router.register("geo_query", GeoQueryViewSet, basename="geo_query")
router.register("address_search", AddressSearchViewSet, basename="address_search")
router.register("user", UserViewSet)
router.register("contract_zone", ContractZoneViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("v1/", include((router.urls, "haravajarjestelma"), namespace="v1")),
    path("helauth/", include("helusers.urls")),
    path("gdpr-api/", include("helsinki_gdpr.urls")),
    # Kubernetes liveness & readiness probes
    path("", include("helsinki_health_endpoints.urls")),
]
