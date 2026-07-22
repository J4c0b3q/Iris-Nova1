from discord.ext import commands

from core.base_cog import BaseCog
from core.module_manager import get_modules
from utils.checks import is_owner


class Load(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)

    @commands.hybrid_command(
        name="load",
        description="Ładuje wszystkie moduły."
    )
    @is_owner()
    async def load(self, ctx: commands.Context):

        loaded = 0
        failed = 0

        for module in get_modules():

            if module in self.bot.extensions:
                continue

            try:
                await self.bot.load_extension(module)
                loaded += 1

            except Exception:
                failed += 1
                self.logger.exception(module)

        await ctx.send(
            f"✅ Załadowano: **{loaded}**\n"
            f"❌ Błędy: **{failed}**"
        )


async def setup(bot):
    await bot.add_cog(Load(bot))