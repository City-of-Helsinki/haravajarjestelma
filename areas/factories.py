import factory.fuzzy
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from factory.random import randgen
from munigeo.models import Address, Municipality, Street

from .models import ContractZone, BlockedDate


class ContractZoneFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("bs")
    email = factory.Faker("email")
    secondary_email = factory.Faker("email")
    boundary = factory.Sequence(
        lambda n: MultiPolygon(
            Polygon(
                ((24 + n, 60), (25 + n, 60), (25 + n, 61), (24 + n, 61), (24 + n, 60))
            )
        )
    )
    origin_id = factory.Sequence(lambda n: n)

    class Meta:
        model = ContractZone


class BlockedDateFactory(factory.django.DjangoModelFactory):
    date = factory.Faker("date_this_year")
    contract_zone = factory.SubFactory(ContractZoneFactory)
    reason = factory.Faker("sentence")

    class Meta:
        model = BlockedDate


# Because of a bug in django-munigeo v0.3.2 we cannot use Django's get_or_create() for
# models that have translated fields, so we need to use this workaround for now.
def _get_or_create_municipality(id):
    try:
        return Municipality.objects.get(id=id)
    except Municipality.DoesNotExist:
        return MunicipalityFactory(id=id)


class MunicipalityFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("city")
    id = factory.Faker("uuid4")

    class Meta:
        model = Municipality


class StreetFactory(factory.django.DjangoModelFactory):
    municipality = factory.LazyFunction(lambda: _get_or_create_municipality("helsinki"))
    name = factory.Faker("street_name")

    class Meta:
        model = Street


class AddressFactory(factory.django.DjangoModelFactory):
    number = factory.LazyFunction(lambda: str(randgen.randint(1, 20)))
    number_end = factory.LazyAttribute(
        lambda o: str(int(o.number) + randgen.randint(1, 5))
    )
    letter = factory.Faker("random_letter")
    street = factory.SubFactory(StreetFactory)
    location = factory.LazyFunction(
        lambda: Point(
            24.915 + randgen.uniform(0, 0.040), 60.154 + randgen.uniform(0, 0.022)
        )
    )

    class Meta:
        model = Address
