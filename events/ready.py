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
            logger.info("Synchronizowanie slash commands z serwerami Discord...")
            synced = await self.bot.tree.sync()
            logger.info(f"🌙 Zsynchronizowano {len(synced)} komend slash.")
        except Exception as e:
            logger.error(f"❌ Błąd synchronizacji slash commands: {e}")

        logger.info(f"✨ {BOT_NAME} v{VERSION} pomyślnie połączony jako {self.bot.user}")
        log_info(f"Bot gotowy do pracy. Gildie: {len(self.bot.guilds)}")


async def setup(bot):
    await bot.add_cog(Ready(bot))