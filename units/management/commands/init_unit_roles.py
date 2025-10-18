from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Initialize roles for Units: create unit_manager and remove chapter-manager if present.'

    def handle(self, *args, **options):
        unit_group, created = Group.objects.get_or_create(name='unit_manager')
        if created:
            self.stdout.write(self.style.SUCCESS("Created group 'unit_manager'"))
        else:
            self.stdout.write("Group 'unit_manager' already exists")

        # Remove chapter-manager role if it exists (both potential names)
        removed_any = False
        for name in ['chapter_manager', 'chapter-manager', 'Chapter Manager']:
            try:
                grp = Group.objects.get(name=name)
                grp.delete()
                removed_any = True
                self.stdout.write(self.style.WARNING(f"Removed deprecated group '{name}'"))
            except Group.DoesNotExist:
                pass

        if not removed_any:
            self.stdout.write("No deprecated chapter manager groups found.")

        self.stdout.write(self.style.SUCCESS('Unit roles initialization complete.'))
