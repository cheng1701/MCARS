from django.apps import AppConfig


class SettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settings'
    verbose_name = 'System Settings'

    def ready(self):
        """
        Connect signals that need to run after migrations. Avoid DB access here.
        """
        from django.db.models.signals import post_migrate

        def create_required_groups(sender=None, **kwargs):
            """Create required Django Groups after migrations complete.
            Also deduplicate legacy events_manager by migrating users to 'Events Manager' and deleting the old group.
            """
            try:
                # Import inside handler to ensure apps are ready
                from django.contrib.auth.models import Group
                from django.db.utils import OperationalError, ProgrammingError

                # Ensure canonical groups exist
                required_groups = [
                    'unit_manager',
                    'rank_manager',
                    'Events Manager',  # canonical name
                ]
                for g in required_groups:
                    Group.objects.get_or_create(name=g)

                # Deduplicate legacy events_manager group if present
                try:
                    canonical, _ = Group.objects.get_or_create(name='Events Manager')
                    legacy = Group.objects.filter(name='events_manager').first()
                    if legacy and legacy.id != canonical.id:
                        # Migrate users
                        for user in legacy.user_set.all():
                            user.groups.add(canonical)
                        # Delete legacy group
                        legacy.delete()
                except Exception:
                    # Be resilient; any failure here should not break migrations
                    pass
            except (OperationalError, ProgrammingError):
                # If the auth tables aren't ready yet, skip; the next post_migrate will handle it.
                pass

        # Connect once; no sender filter so it runs after any app migration
        post_migrate.connect(create_required_groups, dispatch_uid='settings.create_required_groups')