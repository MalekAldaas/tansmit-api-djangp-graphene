from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Create default user groups'

    def handle(self, *args, **kwargs):
        group_names = ['manager', 'organizer', 'driver', 'crew', 'customer']
        for name in group_names:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Group "{name}" created.'))
            else:
                self.stdout.write(f'Group "{name}" already exists.')

