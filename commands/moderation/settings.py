import discord
from discord import app_commands
from discord.ext import commands


class Settings(commands.GroupCog, name="settings"):
    """Komendy konfiguracyjne Iris."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="logs",
        description="Konfiguracja kanału logów"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def logs(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        await interaction.response.send_message(
            f"✅ Kanał logów ustawiony na {channel.mention}",
            ephemeral=True
        )

    @app_commands.command(
        name="welcome",
        description="Konfiguracja kanału powitań"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        await interaction.response.send_message(
            f"✅ Kanał powitań ustawiony na {channel.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Settings(bot))