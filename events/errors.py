from discord.ext import commands

from core.logger import log_info


class ErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if isinstance(error, commands.CommandNotFound):
            return


        if isinstance(error, commands.MissingPermissions):

            await ctx.send(
                "❌ Nie masz uprawnień do użycia tej komendy."
            )

            return


        if isinstance(error, commands.MissingRequiredArgument):

            await ctx.send(
                "❌ Brakuje wymaganego argumentu."
            )

            return


        log_info(
            f"Błąd komendy {ctx.command}: {error}"
        )


        await ctx.send(
            "❌ Wystąpił błąd podczas wykonywania komendy."
        )


async def setup(bot):

    await bot.add_cog(
        ErrorHandler(bot)
    )