from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils import timezone
from datetime import timedelta
from areas.models import ContractZone
from events.models import Event


class Command(BaseCommand):
    help = 'Creates 15 test events with Helsinki addresses'

    def handle(self, *args, **options):
        test_locations = [
            {
                'name': 'Kaivopuiston kevätsiivous',
                'description': 'Siivotaan yhdessä Kaivopuiston alue kevätkuntoon.',
                'lat': 60.1553,
                'lng': 24.9497,
                'address': 'Kaivopuisto, Helsinki',
                'targets': 'Puiston kävelytiet ja nurmikoiden reunat',
                'days_offset': -10,
            },
            {
                'name': 'Kaisaniemen puisto talkoot',
                'description': 'Tule mukaan siivoamaan Kaisaniemen puistoa!',
                'lat': 60.1719,
                'lng': 24.9447,
                'address': 'Kaisaniemenkatu 3, Helsinki',
                'targets': 'Puistoalueet ja penkkien ympäristöt',
                'days_offset': -7,
            },
            {
                'name': 'Töölönlahden rannan siivous',
                'description': 'Pidetään rantaviiva siistinä yhdessä.',
                'lat': 60.1765,
                'lng': 24.9262,
                'address': 'Mannerheimintie 13, Helsinki',
                'targets': 'Rantaviiva ja kävelyreitit',
                'days_offset': -5,
            },
            {
                'name': 'Seurasaaren luontotalkoot',
                'description': 'Seurasaaren ulkoilualueiden kunnostus.',
                'lat': 60.1837,
                'lng': 24.8849,
                'address': 'Seurasaari, Helsinki',
                'targets': 'Luontopolut ja levähdyspaikat',
                'days_offset': -3,
            },
            {
                'name': 'Esplanadin puiston hoito',
                'description': 'Kevätkunnostus keskustan viheroaasissa.',
                'lat': 60.1672,
                'lng': 24.9463,
                'address': 'Esplanadi, Helsinki',
                'targets': 'Kukkapenkit ja istutusalueet',
                'days_offset': 2,
            },
            {
                'name': 'Hakaniemen torin ympäristö',
                'description': 'Siivotaan torin ympäristö ja viheralueet.',
                'lat': 60.1794,
                'lng': 24.9508,
                'address': 'Hakaniementori 1, Helsinki',
                'targets': 'Torin reunat ja viheralueet',
                'days_offset': 5,
            },
            {
                'name': 'Pihlajamäen metsätalkoot',
                'description': 'Metsäpolkujen kunnostus ja roskien keräys.',
                'lat': 60.2543,
                'lng': 25.0834,
                'address': 'Pihlajamäki, Helsinki',
                'targets': 'Metsäpolut ja ulkoilureitit',
                'days_offset': 7,
            },
            {
                'name': 'Aurinkolahden rantasiivous',
                'description': 'Pidetään ranta-alueet puhtaina.',
                'lat': 60.2102,
                'lng': 25.1472,
                'address': 'Aurinkolahti, Helsinki',
                'targets': 'Ranta-alueet ja uimarannat',
                'days_offset': 10,
            },
            {
                'name': 'Meilahden ulkoilualue',
                'description': 'Ulkoilureittien kunnostus ja siivous.',
                'lat': 60.1889,
                'lng': 24.9058,
                'address': 'Meilahdentie 2, Helsinki',
                'targets': 'Ulkoilureitit ja leikkipaikat',
                'days_offset': 14,
            },
            {
                'name': 'Herttoniemen rantapuisto',
                'description': 'Yhteisöllinen kevätsiivous rantapuistossa.',
                'lat': 60.1954,
                'lng': 25.0342,
                'address': 'Hitsaajankatu 10, Helsinki',
                'targets': 'Rantapuisto ja virkistysalueet',
                'days_offset': 17,
            },
            {
                'name': 'Töölön pallokentän ympäristö',
                'description': 'Pallokentän ja sen ympäristön siivous.',
                'lat': 60.1819,
                'lng': 24.9224,
                'address': 'Töölön pallokenttä, Helsinki',
                'targets': 'Urheilualueet ja ympäröivät viheralueet',
                'days_offset': 21,
            },
            {
                'name': 'Kalasataman puistotalkoot',
                'description': 'Uuden asuinalueen viheralueiden hoito.',
                'lat': 60.1891,
                'lng': 24.9775,
                'address': 'Sörnäistenkatu 1, Helsinki',
                'targets': 'Puistoalueet ja leikkikentät',
                'days_offset': 25,
            },
            {
                'name': 'Talin lähimetsän kunnostus',
                'description': 'Lähimetsän polkujen ja oleskelualueiden siivous.',
                'lat': 60.2165,
                'lng': 24.8213,
                'address': 'Tali, Helsinki',
                'targets': 'Metsäpolut ja oleskelualueet',
                'days_offset': 28,
            },
            {
                'name': 'Lauttasaaren Vattuvuoren talkoot',
                'description': 'Vattuvuoren ulkoilualueen kevätkunnostus.',
                'lat': 60.1577,
                'lng': 24.8659,
                'address': 'Vattuniemenranta, Helsinki',
                'targets': 'Ulkoilualueet ja kallioreitit',
                'days_offset': 35,
            },
            {
                'name': 'Viikki-Vanhankaupunginlahti luontotalkoot',
                'description': 'Luonnonsuojelualueen hoitotalkoot.',
                'lat': 60.2267,
                'lng': 25.0186,
                'address': 'Viikki, Helsinki',
                'targets': 'Luontopolut ja lintutornin ympäristö',
                'days_offset': 42,
            },
        ]

        try:
            contract_zone = ContractZone.objects.filter(active=True).first()
            if not contract_zone:
                self.stdout.write(
                    self.style.ERROR('No active contract zones found. Please create one first.')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error fetching contract zone: {e}')
            )
            return

        created_count = 0
        now = timezone.now()

        for i, location in enumerate(test_locations, start=1):
            try:
                start_time = now + timedelta(days=location['days_offset'])
                end_time = start_time + timedelta(hours=3)

                point = Point(location['lng'], location['lat'], srid=4326)

                try:
                    actual_zone = ContractZone.objects.get_active_by_location(point)
                    if actual_zone:
                        contract_zone = actual_zone
                except Exception:
                    pass

                event = Event.objects.create(
                    name=location['name'],
                    description=location['description'],
                    start_time=start_time,
                    end_time=end_time,
                    location=point,
                    organizer_first_name='Testi',
                    organizer_last_name=f'Järjestäjä {i}',
                    organizer_email=f'testi{i}@example.com',
                    organizer_phone=f'+35840123{i:04d}',
                    estimated_attendee_count=10 + (i * 2),
                    targets=location['targets'],
                    maintenance_location=location['address'],
                    additional_information='Tämä on testidataa.',
                    small_trash_bag_count=15 + i,
                    large_trash_bag_count=5 + i,
                    trash_picker_count=10 + i,
                    equipment_information='Omat käsineet suositeltavia.',
                    contract_zone=contract_zone,
                    state=Event.APPROVED,
                )

                created_count += 1
                status = '✓ Past' if location['days_offset'] < 0 else '✓ Future'
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{status} {i}/15: {event.name} ({event.start_time.strftime('%Y-%m-%d')})"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error creating event {i}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count}/15 test events')
        )
