from discord.ext import commands
from core.logger import log_error


class Errors(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "❌ Nie masz uprawnień do użycia tej komendy."
            )

            log_error(
                f"{ctx.author} próbował użyć {ctx.command} bez uprawnień"
            )


        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "❌ Brakuje argumentu do tej komendy."
            )


        elif isinstance(error, commands.CommandNotFound):
            pass


        else:
            await ctx.send(
                "⚠️ Wystąpił nieoczekiwany błąd."
            )

            log_error(
                f"Błąd komendy {ctx.command}: {error}"
            )


async def setup(bot):
    await bot.add_cog(Errors(bot))