from django.core.management.base import BaseCommand

from areas.importer.helsinki import HelsinkiImporter


class Command(BaseCommand):
    help = "Import Helsinki contract zones"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true", help="Skip deletion sanity check"
        )

    def handle(self, *args, **options):
        HelsinkiImporter().import_contract_zones(options["force"])
