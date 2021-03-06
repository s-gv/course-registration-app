from django.core.management.base import BaseCommand, CommandError
from coursereg.models import Department
import json

class Command(BaseCommand):
    help = 'Bulk load departments to the database from a JSON file.'

    def add_arguments(self, parser):
        parser.add_argument('--datafile',
            default='coursereg/data/depts.json',
            help='File to load data from (default: coursereg/data/depts.json)')

    def handle(self, *args, **options):
        with open(options['datafile']) as f:
            depts = json.loads(f.read())
            counter = 0
            for dept in depts:
                dept_name = dept['name']
                dept_abbreviation = dept['abbreviation']
                is_active = dept['is_active']
                if not Department.objects.filter(abbreviation=dept_abbreviation):
                    Department.objects.create(name=dept_name, abbreviation=dept_abbreviation, is_active=is_active)
                    counter += 1
            self.stdout.write(self.style.SUCCESS(
                'Successfully added %s departments to the databse.' % (counter, )
            ))                                                                                
