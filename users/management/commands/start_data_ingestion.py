
from django.core.management.base import BaseCommand
from users.views import ingest_data

class Command(BaseCommand):
    help = 'Starts data ingestion process'

    def handle(self, *args, **options):
        ingest_data(None) 
        self.stdout.write(self.style.SUCCESS('Data ingestion process started'))
