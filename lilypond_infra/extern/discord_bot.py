import os
from functools import wraps

import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

BOT_API = os.environ.get("BOT_SERVICE_URL", "http://127.0.0.1:8001")


def user_has_role(user, role_id):
    try:
        discord_account = user.socialaccount_set.get(provider="discord")
        user_id = int(discord_account.uid)
        print(BOT_API)
        response = requests.get(f"{BOT_API}/member/{user_id}/has-role/{role_id}")
        data = response.json()

        return data.get("has_role", False)
    except SocialAccount.DoesNotExist:
        return False


def discord_role_required(role_id):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            try:
                discord_account = request.user.socialaccount_set.get(provider="discord")
                user_id = int(discord_account.uid)

                # this is a local request, but it *could* be outgoing/to discord
                # caching is good enough to do this everywhere I hope?
                response = requests.get(
                    f"{BOT_API}/member/{user_id}/has-role/{role_id}"
                )
                data = response.json()
            except SocialAccount.DoesNotExist, requests.RequestException:
                return HttpResponseForbidden("Unable to verify Discord membership.")

            if not data.get("in_server"):
                return HttpResponseForbidden("You are not in the RAW Discord server.")
            if not data.get("has_role"):
                return HttpResponseForbidden(
                    "You are missing a Discord role that is required to access this page."
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
