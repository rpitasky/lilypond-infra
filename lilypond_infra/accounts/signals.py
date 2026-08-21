from allauth.account.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import Group

import discord_settings
from extern import discord_bot


@receiver(user_logged_in)
def add_user_to_admin_group(sender, request, user, **kwargs):
    admin_group, created = Group.objects.get_or_create(name="Admin")

    if (
        user.is_staff
        or user.is_superuser
        or discord_bot.user_has_role(
            user, discord_settings.LILYPOND_TEAM_LEAD_ROLE_ID
        )
        or discord_bot.user_has_role(user, discord_settings.ED_BOARD_ROLE_ID)
    ):
        user.groups.add(admin_group)
        if not user.is_staff:
            user.is_staff = True
            user.save()
    else:
        user.groups.remove(admin_group)
        if user.is_staff:
            user.is_staff = False
            user.save()
