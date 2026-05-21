"""AppConfig for the user_profiles application."""

from django.apps import AppConfig


class UserProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.user_profiles"
    verbose_name = "User Profiles"

    def ready(self) -> None:
        # Register signal handlers.
        import apps.user_profiles.signals  # noqa: F401
