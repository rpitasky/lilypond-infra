import os
import sys

import discord
import asyncio
import uvicorn
from fastapi import FastAPI

DISCORD_SERVER_ID = 1370472564433883146

intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)
api = FastAPI()

HOST = "0.0.0.0" if "--docker" in sys.argv else "127.0.0.1"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@api.get('/member/{user_id}/has-role/{role_id}')
async def has_role(user_id: int, role_id: int):
    print(f"Checking if user {user_id} has role {role_id}")
    guild = bot.get_guild(DISCORD_SERVER_ID)
    if not guild:
        return {'error': 'Guild not found'}

    member = guild.get_member(user_id)
    if not member:
        return {'in_server': False, 'has_role': False}

    return {
        'in_server': True,
        'has_role': any(role.id == role_id for role in member.roles),
    }


async def start_api():
    config = uvicorn.Config(api, host=HOST, port=8001, log_level='error')
    server = uvicorn.Server(config)
    print('Starting API server on port 8001')
    await server.serve()


async def main():
    await asyncio.gather(
        bot.start(os.environ.get("DISCORD_BOT_TOKEN")),
        start_api(),
    )


if __name__ == '__main__':
    asyncio.run(main())