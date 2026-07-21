import discord
from discord.ext import commands

from core.logger import log_error


class Errors(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



    @commands.Cog.listener()
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error
    ):


        if isinstance(
            error,
            discord.app_commands.MissingPermissions
        ):

            message = (
                "❌ Nie masz uprawnień "
                "do użycia tej komendy."
            )


            log_error(
                f"{interaction.user} próbował użyć "
                f"/{interaction.command.name} bez uprawnień"
            )



        elif isinstance(
            error,
            discord.app_commands.CommandOnCooldown
        ):

            message = (
                f"⏳ Ta komenda jest na cooldownie.\n"
                f"Spróbuj ponownie za "
                f"{error.retry_after:.1f}s."
            )



        elif isinstance(
            error,
            discord.app_commands.CommandSignatureMismatch
        ):

            message = (
                "❌ Nieprawidłowe użycie komendy."
            )



        else:

            message = (
                "⚠️ Wystąpił nieoczekiwany błąd."
            )


            log_error(
                f"Błąd slash command "
                f"/{interaction.command.name}: {error}"
            )



        embed = discord.Embed(
            title="🌙 Iris Nova — Błąd",
            description=message,
            color=discord.Color.red()
        )


        if interaction.response.is_done():

            await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )



    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx,
        error
    ):


        if isinstance(
            error,
            commands.MissingPermissions
        ):

            await ctx.send(
                "❌ Nie masz uprawnień do użycia tej komendy."
            )


        elif isinstance(
            error,
            commands.MissingRequiredArgument
        ):

            await ctx.send(
                "❌ Brakuje argumentu do tej komendy."
            )


        elif isinstance(
            error,
            commands.CommandNotFound
        ):

            return


        else:

            await ctx.send(
                "⚠️ Wystąpił nieoczekiwany błąd."
            )


            log_error(
                f"Błąd komendy {ctx.command}: {error}"
            )



async def setup(bot):

    await bot.add_cog(
        Errors(bot)
    )