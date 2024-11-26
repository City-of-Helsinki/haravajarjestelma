import factory.fuzzy
from datetime import timedelta
from django.contrib.gis.geos import Point
from django.utils import timezone
from factory.random import randgen

from areas.factories import ContractZoneFactory

from .models import Event


class EventFactory(factory.django.DjangoModelFactory):
    state = Event.APPROVED
    name = factory.Faker("bs")
    description = factory.Faker("text")
    start_time = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=8, hours=randgen.randint(1, 6))
    )
    end_time = factory.LazyAttribute(
        lambda e: e.start_time + timedelta(hours=randgen.randint(1, 6))
    )
    organizer_first_name = factory.Faker("first_name")
    organizer_last_name = factory.Faker("last_name")
    organizer_email = factory.Faker("email")
    organizer_phone = factory.Faker("phone_number")
    estimated_attendee_count = factory.fuzzy.FuzzyInteger(1, 100)
    targets = factory.Faker("text")
    maintenance_location = factory.Faker("address")
    additional_information = factory.Faker("text")
    small_trash_bag_count = factory.fuzzy.FuzzyInteger(1, 500)
    large_trash_bag_count = factory.fuzzy.FuzzyInteger(1, 500)
    trash_picker_count = factory.fuzzy.FuzzyInteger(1, 50)
    equipment_information = factory.Faker("text")
    contract_zone = factory.SubFactory(ContractZoneFactory)

    class Meta:
        model = Event

    @factory.lazy_attribute
    def location(self):
        centroid = self.contract_zone.boundary[0].centroid
        return Point(
            centroid.x + randgen.uniform(0, 0.040),
            centroid.y + randgen.uniform(0, 0.022),
        )
