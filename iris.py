print("Start Iris")

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

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


async def main():

    init_database()

    async with bot:

        await load_extensions(bot)

        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())