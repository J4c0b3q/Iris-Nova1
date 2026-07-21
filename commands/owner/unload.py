from discord.ext import commands

from core.logger import get_logger
from utils.checks import is_owner

logger = get_logger(__name__)


class Unload(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="unload")
    @is_owner()
    async def unload(self, ctx, module: str):

        try:

            await self.bot.unload_extension(module)

            await ctx.send("✅ Done")

        except Exception:

            logger.exception(module)

            await ctx.send("❌ Error")


async def setup(bot):
    await bot.add_cog(Unload(bot))