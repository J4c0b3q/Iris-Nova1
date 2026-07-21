print("🌙 Start Iris Nova")


import discord
from discord.ext import commands

from dotenv import load_dotenv

import os
import asyncio


from core.config import (
    PREFIX,
    BOT_NAME,
    VERSION
)

from core.logger import log_info
from core.database import init_database
from core.loader import load_extensions



load_dotenv()


TOKEN = os.getenv(
    "DISCORD_TOKEN"
)



if not TOKEN:

    raise Exception(
        "❌ Brak DISCORD_TOKEN w pliku .env"
    )



intents = discord.Intents.all()



bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)



@bot.event
async def on_ready():

    print(
        f"🌙 {BOT_NAME} v{VERSION}"
        f" online jako {bot.user}"
    )

    log_info(
        f"{BOT_NAME} uruchomiony jako {bot.user}"
    )



async def main():


    print(
        "📦 Inicjalizacja bazy danych..."
    )


    init_database()



    print(
        "🔌 Ładowanie modułów..."
    )


    async with bot:


        await load_extensions(bot)


        print(
            "🚀 Łączenie z Discord..."
        )


        await bot.start(
            TOKEN
        )



if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )


    except KeyboardInterrupt:

        print(
            "🛑 Iris zatrzymany"
        )