import discord
import asyncio
import uvicorn
from fastapi import FastAPI
import discord_settings


intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)
api = FastAPI()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@api.get('/member/{user_id}/has-role/{role_id}')
async def has_role(user_id: int, role_id: int):
    guild = bot.get_guild(discord_settings.DISCORD_SERVER_ID)
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
    config = uvicorn.Config(api, host='127.0.0.1', port=8001, log_level='error')
    server = uvicorn.Server(config)
    print('Starting API server on port 8001')
    await server.serve()


async def main():
    await asyncio.gather(
        bot.start(discord_settings.DISCORD_BOT_TOKEN),
        start_api(),
    )


if __name__ == '__main__':
    asyncio.run(main())