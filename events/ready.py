import discord
from discord.ext import commands

from core.config import BOT_NAME, VERSION
from core.logger import get_logger, log_info

logger = get_logger("ReadyEvent")


class Ready(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._synced = False

    @commands.Cog.listener()
    async def on_ready(self):
        if self._synced:
            return

        try:
            await self.bot.change_presence(
                activity=discord.Game(
                    name=f"/help | {BOT_NAME}"
                )
            )
            logger.info("🔎 Synchronizowanie slash commands...")
            synced_global = await self.bot.tree.sync()
            logger.info(f"🌙 Zsynchronizowano globalnie: {len(synced_global)} slash commands")

            # Kopiowanie i natychmiastowa synchronizacja dla każdego serwera bota
            for guild in self.bot.guilds:
                try:
                    self.bot.tree.copy_global_to(guild=guild)
                    synced_guild = await self.bot.tree.sync(guild=guild)
                    logger.info(f"⚡ Zsynchronizowano {len(synced_guild)} komend dla serwera: {guild.name}")
                except Exception as g_err:
                    logger.warning(f"⚠️ Nie udało się zsynchronizować komend dla {guild.name}: {g_err}")

            self._synced = True
        except Exception as e:
            logger.error(f"❌ Błąd synchronizacji slash commands: {e}")

        logger.info(f"{BOT_NAME} v{VERSION} działa jako {self.bot.user}")
        log_info(f"Bot uruchomiony jako {self.bot.user}")


async def setup(bot):
    await bot.add_cog(Ready(bot))