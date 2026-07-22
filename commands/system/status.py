import time

import discord
from discord import app_commands

from core.base_cog import BaseCog
from core.config import BOT_NAME, VERSION, SETTINGS
from core.constants import EMBED_COLOR

START_TIME = time.time()


class Status(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @discord.ext.commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(
            activity=discord.Game(
                name=f"/help | {BOT_NAME}"
            )
        )

    @app_commands.command(
        name="status",
        description="Pokazuje status Iris."
    )
    async def status(
        self,
        interaction: discord.Interaction,
    ):

        uptime = int(time.time() - START_TIME)

        hours = uptime // 3600
        minutes = (uptime % 3600) // 60

        members = sum(
            guild.member_count or 0
            for guild in self.bot.guilds
        )

        embed = discord.Embed(
            title=f"🌙 {BOT_NAME}",
            color=EMBED_COLOR,
        )

        embed.add_field(
            name="Status",
            value="🟢 Online",
            inline=False,
        )

        embed.add_field(
            name="Czas działania",
            value=f"{hours}h {minutes}m",
            inline=True,
        )

        embed.add_field(
            name="Serwery",
            value=str(len(self.bot.guilds)),
            inline=True,
        )

        embed.add_field(
            name="Użytkownicy",
            value=str(members),
            inline=True,
        )

        embed.add_field(
            name="AI",
            value="🟢 ON" if SETTINGS["AI_ENABLED"] else "🔴 OFF",
            inline=True,
        )

        embed.add_field(
            name="Wersja",
            value=VERSION,
            inline=True,
        )

        embed.set_footer(
            text="Iris Nova"
        )

        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(Status(bot))