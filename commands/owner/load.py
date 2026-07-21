from discord.ext import commands

from core.logger import get_logger
from core.module_manager import get_modules
from utils.checks import is_owner

logger = get_logger(__name__)


class Load(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="load")
    @is_owner()
    async def load(self, ctx):

        ok = 0

        for module in get_modules():

            try:
                await self.bot.load_extension(module)
                ok += 1

            except Exception:
                logger.exception(module)

        await ctx.send(f"Loaded {ok} modules")


async def setup(bot):
    await bot.add_cog(Load(bot))