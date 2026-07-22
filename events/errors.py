from discord.ext import commands
from core.logger import log_error, log_info


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        # Ignoruj nieistniejące komendy
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Nie masz wystarczających uprawnień do użycia tej komendy.")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Brakuje wymaganego argumentu: `{error.param.name}`")
            return

        # Rejestrowanie poważniejszych błędów
        log_error(f"Błąd komendy {ctx.command}: {error}", exc_info=True)
        await ctx.send("❌ Wystąpił nieoczekiwany błąd podczas wykonywania komendy.")


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))