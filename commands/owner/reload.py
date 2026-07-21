from discord.ext import commands

from core.logger import get_logger
from core.module_manager import get_modules
from utils.checks import is_owner

logger = get_logger(__name__)


class Reload(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="reload")
    @is_owner()
    async def reload(self, ctx):

        ok = 0
        failed = 0

        for module in get_modules():

            try:
                await self.bot.reload_extension(module)
                ok += 1

            except Exception:
                logger.exception(module)
                failed += 1

        await ctx.send(
            f"✅ Reloaded: {ok}\n❌ Failed: {failed}"
        )


async def setup(bot):
    await bot.add_cog(Reload(bot))