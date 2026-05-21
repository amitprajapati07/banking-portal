"""Auto-create and keep UserProfile in sync with Django's User model."""

import logging

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.user_profiles.models import UserProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_or_save_user_profile(
    sender: type,
    instance: User,
    created: bool,
    **kwargs,
) -> None:
    """
    Signal handler that fires after every ``User.save()``.

    - On first creation: builds a new ``UserProfile``.
    - On subsequent saves: persists any changes to the related profile
      (e.g. ``UPDATE_LAST_LOGIN`` via SimpleJWT).
    """
    if created:
        UserProfile.objects.create(user=instance)
        logger.info(
            "UserProfile auto-created for new user pk=%s username=%s",
            instance.pk,
            instance.username,
        )
    else:
        # Guard against edge-cases where the profile was somehow deleted.
        profile, was_created = UserProfile.objects.get_or_create(
            user=instance
        )
        if was_created:
            logger.warning(
                "UserProfile was missing for user pk=%s; re-created.",
                instance.pk,
            )
        else:
            profile.save()
