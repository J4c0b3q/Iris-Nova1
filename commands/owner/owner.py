import discord
from discord.ext import commands
from core.config import OWNER_ID
from core.logger import log_info

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID

    @discord.app_commands.command(
        name="ownerstats",
        description="Statystyki administracyjne bota dla właściciela"
    )
    async def ownerstats(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Brak dostępu.", ephemeral=True)
            return

        embed = discord.Embed(
            title="👑 Panel Właściciela Iris",
            description=f"Witaj, <@{OWNER_ID}>! Wszystkie moduły działają poprawnie.",
            color=discord.Color.gold()
        )
        embed.add_field(name="Gildie", value=str(len(self.bot.guilds)))
        embed.add_field(name="Moduły", value=str(self.bot.loaded_modules))
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Owner(bot))