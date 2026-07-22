import discord
from discord.ext import commands
import platform

from core.config import OWNER_ID
from core.env import Env


class Owner(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def check_owner(self, user: discord.User | discord.Member) -> bool:
        """Sprawdza czy użytkownik jest właścicielem bota (za pomocą Env, config lub Discord Application info)."""
        if Env.OWNER_ID and user.id == Env.OWNER_ID:
            return True
        if OWNER_ID and user.id == OWNER_ID:
            return True
        return await self.bot.is_owner(user)

    @discord.app_commands.command(
        name="ownerstats",
        description="Wyświetla szczegółowe statystyki bota przeznaczone dla właściciela"
    )
    async def ownerstats(self, interaction: discord.Interaction):
        if not await self.check_owner(interaction.user):
            await interaction.response.send_message(
                "❌ Brak dostępu. Ta komenda jest dostępna tylko dla właściciela bota.",
                ephemeral=True
            )
            return

        guild_count = len(self.bot.guilds)
        total_users = sum(g.member_count or len(g.members) for g in self.bot.guilds)
        latency = round(self.bot.latency * 1000)
        extensions_count = len(self.bot.extensions)

        embed = discord.Embed(
            title="📊 Panel Właściciela • Statystyki Iris Nova",
            color=discord.Color.gold()
        )

        embed.add_field(name="🌐 Serwery", value=f"**{guild_count}** serwerów", inline=True)
        embed.add_field(name="👥 Użytkownicy", value=f"**{total_users}** osób", inline=True)
        embed.add_field(name="⚡ Ping", value=f"**{latency} ms**", inline=True)

        embed.add_field(name="📦 Moduły (Extensions)", value=f"**{extensions_count}** załadowanych", inline=True)
        embed.add_field(name="🐍 Wersja Python", value=f"`{platform.python_version()}`", inline=True)
        embed.add_field(name="⚙️ discord.py", value=f"`{discord.__version__}`", inline=True)

        embed.set_footer(
            text=f"🌙 Iris Nova • Dostęp autoryzowany dla {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Owner(bot))