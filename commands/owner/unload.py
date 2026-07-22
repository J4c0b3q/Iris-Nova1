from discord.ext import commands

from core.base_cog import BaseCog
from utils.checks import is_owner


class Unload(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)

    @commands.hybrid_command(
        name="unload",
        description="Wyłącza wybrany moduł."
    )
    @is_owner()
    async def unload(
        self,
        ctx: commands.Context,
        module: str,
    ):
        # Odroczenie interakcji
        await ctx.defer()

        try:

            await self.bot.unload_extension(module)

            await ctx.send(
                f"✅ Wyłączono `{module}`"
            )

        except Exception:

            self.logger.exception(module)

            await ctx.send(
                f"❌ Nie udało się wyłączyć `{module}`"
            )


async def setup(bot):
    await bot.add_cog(Unload(bot))