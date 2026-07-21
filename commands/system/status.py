import discord
from discord.ext import commands

from core.config import BOT_NAME, VERSION, SETTINGS

import time


start_time = time.time()


class Status(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):

        await self.bot.change_presence(
            activity=discord.Game(
                name=f"/help | {BOT_NAME}"
            )
        )


    @discord.app_commands.command(
        name="status",
        description="Pokazuje status Iris"
    )
    async def status(
        self,
        interaction: discord.Interaction
    ):


        uptime = int(
            time.time() - start_time
        )


        hours = uptime // 3600
        minutes = (uptime % 3600) // 60


        members = sum(
            g.member_count or 0
            for g in self.bot.guilds
        )


        ai_status = (
            "🟢 ON"
            if SETTINGS["AI_ENABLED"]
            else "🔴 OFF"
        )


        embed = discord.Embed(
            title=f"🌙 {BOT_NAME}",
            color=discord.Color.green()
        )


        embed.add_field(
            name="🟢 Status",
            value="Online",
            inline=False
        )


        embed.add_field(
            name="⏱️ Czas działania",
            value=f"{hours}h {minutes}m",
            inline=True
        )


        embed.add_field(
            name="🌐 Serwery",
            value=str(len(self.bot.guilds)),
            inline=True
        )


        embed.add_field(
            name="👥 Użytkownicy",
            value=str(members),
            inline=True
        )


        embed.add_field(
            name="🧠 AI",
            value=ai_status,
            inline=True
        )


        embed.add_field(
            name="⚙️ Wersja",
            value=VERSION,
            inline=True
        )


        await interaction.response.send_message(
            embed=embed
        )



async def setup(bot):

    await bot.add_cog(
        Status(bot)
    )