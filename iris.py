print("Start Iris")

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import asyncio

from core.personality import IRIS_PERSONALITY
from core.config import PREFIX, BOT_NAME, VERSION
from core.logger import log_info
from core.database import init_database
from core.loader import load_extensions

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)

@bot.event
async def on_ready():

    print("🔍 Komendy Iris:")

    for cmd in bot.tree.get_commands():
        print(f" - {cmd.name}")


    guild = discord.Object(
        id=1529094841227808809
    )

    try:

        # usuwa stare komendy tylko na serwerze testowym
        bot.tree.clear_commands(
            guild=guild
        )

        synced = await bot.tree.sync(
            guild=guild
        )

        print(
            f"🌙 Zsynchronizowano {len(synced)} slash commands"
        )

    except Exception as e:

        print(
            f"❌ Błąd synchronizacji slash: {e}"
        )


    print(
        f"{BOT_NAME} v{VERSION} działa jako {bot.user}"
    )

    log_info(
        f"Bot uruchomiony jako {bot.user}"
    )
    

async def main():
    init_database()
    async with bot:

        await load_extensions(bot)
        
        await bot.start(TOKEN)
        

asyncio.run(main())