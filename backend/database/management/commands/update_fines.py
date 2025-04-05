from django.core.management.base import BaseCommand
from backend.database.models import Fines

class Command(BaseCommand):
    help = 'Update all fines in the system'
    
    def handle(self, *args, **options):
        Fines.update_all_fines()
        self.stdout.write('Successfully updated all fines')
