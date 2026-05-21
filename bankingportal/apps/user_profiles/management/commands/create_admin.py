import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decouple import config

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Creates a superuser automatically from environment variables if it does not exist."

    def handle(self, *args, **options):
        username = config('ADMIN_USERNAME', default=None)
        email = config('ADMIN_EMAIL', default=None)
        password = config('ADMIN_PASSWORD', default=None)

        if not all([username, email, password]):
            self.stdout.write(self.style.WARNING("Superuser credentials not fully provided in environment. Skipping."))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' already exists."))
            return

        try:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Successfully created superuser '{username}'."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating superuser: {e}"))
            logger.exception("Failed to create superuser")
