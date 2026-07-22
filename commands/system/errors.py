import discord
from discord.ext import commands

from core.base_cog import BaseCog
from core.constants import ERROR_COLOR


class Errors(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: Exception
    ):

        if isinstance(error, discord.app_commands.MissingPermissions):
            message = "❌ Nie masz uprawnień do użycia tej komendy."

        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            message = (
                f"⏳ Ta komenda jest na cooldownie.\n"
                f"Spróbuj ponownie za {error.retry_after:.1f}s."
            )

        elif isinstance(error, discord.app_commands.CommandSignatureMismatch):
            message = "❌ Nieprawidłowe użycie komendy."

        else:
            self.logger.exception(error)
            message = "⚠️ Wystąpił nieoczekiwany błąd."

        embed = discord.Embed(
            title="Błąd",
            description=message,
            color=ERROR_COLOR,
        )

        if interaction.response.is_done():
            await interaction.followup.send(
                embed=embed,
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: Exception
    ):

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Nie masz uprawnień.")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Brakuje argumentu.")
            return

        self.logger.exception(error)

        await ctx.send("⚠️ Wystąpił nieoczekiwany błąd.")


async def setup(bot):
    await bot.add_cog(Errors(bot))