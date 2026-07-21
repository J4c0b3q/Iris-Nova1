import asyncio

import discord
from discord.ext import commands

from core.config import BOT_NAME, PREFIX, VERSION
from database.database import init_database
from core.env import Env
from core.loader import load_extensions
from core.logger import get_logger

logger = get_logger("Iris")

from core.bot import IrisBot

bot = IrisBot()


@bot.event
async def on_ready():
    logger.info("=" * 60)
    logger.info(f"{BOT_NAME} v{VERSION}")
    logger.info(f"Logged in as: {bot.user} ({bot.user.id})")
    logger.info(f"Guilds: {len(bot.guilds)}")
    logger.info("=" * 60)


async def main():
    logger.info("Starting Iris...")

    logger.info("Initializing database...")
    init_database()

    logger.info("Loading extensions...")
    
    async with bot:
        await load_extensions(bot)

        logger.info("Connecting to Discord...")
        await bot.start(Env.DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.warning("Bot stopped by user (KeyboardInterrupt).")

    except Exception:
        logger.exception("Fatal error while starting Iris.")