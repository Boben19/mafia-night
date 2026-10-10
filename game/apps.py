from django.apps import AppConfig
from django.core.management import call_command
from django.db.models.signals import post_migrate


def load_defaults(sender, **kwargs):
    """A fresh or empty database gets the constitution's roles and rules automatically."""
    from .models import Role, Rule
    if not Role.objects.exists() or not Rule.objects.exists():
        call_command("seed_game", verbosity=0)


class GameConfig(AppConfig):
    name = "game"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        post_migrate.connect(load_defaults, sender=self)
