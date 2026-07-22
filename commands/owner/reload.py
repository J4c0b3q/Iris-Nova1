from discord.ext import commands

from core.base_cog import BaseCog
from core.module_manager import get_modules
from utils.checks import is_owner


class Reload(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)

    @commands.hybrid_command(
        name="reload",
        description="Przeładowuje wszystkie moduły."
    )
    @is_owner()
    async def reload(self, ctx: commands.Context):

        loaded = 0
        failed = 0

        for module in get_modules():

            try:
                if module in self.bot.extensions:
                    await self.bot.reload_extension(module)
                else:
                    await self.bot.load_extension(module)

                loaded += 1

            except Exception:
                failed += 1
                self.logger.exception(module)

        await ctx.send(
            f"♻️ Przeładowano: **{loaded}**\n"
            f"❌ Błędy: **{failed}**"
        )


async def setup(bot):
    await bot.add_cog(Reload(bot))