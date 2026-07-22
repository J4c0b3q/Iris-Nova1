import asyncio

from core.bot import IrisBot
from core.config import BOT_NAME, VERSION
from core.env import Env
from core.logger import get_logger

from database.database import init_database
from database.repositories.guild_repository import GuildRepository
from database.repositories.warning_repository import WarningRepository

logger = get_logger("Iris")

bot = IrisBot()


@bot.event
async def on_ready():
    logger.info("=" * 60)
    logger.info(f"{BOT_NAME} v{VERSION}")
    logger.info(f"Logged in as: {bot.user} ({bot.user.id})")
    logger.info(f"Guilds: {len(bot.guilds)}")
    logger.info(f"Users: {sum(g.member_count or 0 for g in bot.guilds)}")
    logger.info("=" * 60)


async def main():
    logger.info("Starting Iris...")

    # Inicjalizacja bazy danych
    bot.database = init_database()

    # Repositories
    bot.guilds_repo = GuildRepository(bot.database)
    bot.warnings_repo = WarningRepository(bot.database)

    logger.info("Database initialized.")

    async with bot:
        logger.info("Connecting to Discord...")
        await bot.start(Env.DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.warning("Bot stopped by user.")

    except Exception:
        logger.exception("Fatal error while starting Iris.")