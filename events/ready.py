import discord
from discord.ext import commands

from core.config import BOT_NAME, VERSION
from core.logger import get_logger, log_info

logger = get_logger("ReadyEvent")


class Ready(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            await self.bot.change_presence(
                activity=discord.Game(
                    name=f"/help | {BOT_NAME}"
                )
            )
            logger.info("🔎 Synchronizowanie slash commands...")
            synced = await self.bot.tree.sync()
            logger.info(f"🌙 Zsynchronizowano {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"❌ Błąd synchronizacji slash commands: {e}")

        logger.info(f"{BOT_NAME} v{VERSION} działa jako {self.bot.user}")
        log_info(f"Bot uruchomiony jako {self.bot.user}")


async def setup(bot):
    await bot.add_cog(Ready(bot))