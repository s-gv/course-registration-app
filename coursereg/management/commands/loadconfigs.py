from django.core.management.base import BaseCommand, CommandError
from coursereg.models import Config
import json

class Command(BaseCommand):
    help = 'Bulk load config to the database from a JSON file.'

    def add_arguments(self, parser):
        parser.add_argument('--datafile',
            default='coursereg/data/configs.json',
            help='File to load data from (default: coursereg/data/configs.json)')

    def handle(self, *args, **options):
        with open(options['datafile']) as f:
            configs = json.loads(f.read())
            counter = 0
            for config in configs:
                key = config['key']
                value = config['value']
                if not Config.objects.filter(key=key):
                    Config.objects.create(key=key, value=value)
                    counter += 1
            self.stdout.write(self.style.SUCCESS(
                'Successfully added %s configs to the databse.' % (counter, )
            ))            
