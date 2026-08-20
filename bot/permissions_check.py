import discord_settings
from .discord_bot import bot
from allauth.socialaccount.models import SocialAccount


def get_member(user):
    try:
        discord_account = user.socialaccount_set.get(provider='discord')
        guild = bot.get_guild(discord_settings.DISCORD_SERVER_ID)
        if guild:
            return guild.get_member(int(discord_account.uid))
        return None
    except SocialAccount.DoesNotExist:
        return None

def user_has_role(user, role_id):
    member = get_member(user)
    if not member:
        return False
    return any(role.id == role_id for role in member.roles)

