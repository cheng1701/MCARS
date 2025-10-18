from django.apps import AppConfig


class UnitsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'units'

    def ready(self):
        # Place for signals in the future
        pass
