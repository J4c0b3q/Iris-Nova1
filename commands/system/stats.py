import discord
from discord.ext import commands
from core.stats import get_uptime


class Stats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @discord.app_commands.command(
        name="stats",
        description="Pokazuje statystyki Iris"
    )
    async def stats(
        self,
        interaction: discord.Interaction
    ):

        guilds = len(self.bot.guilds)

        users = len(
            set(
                user
                for guild in self.bot.guilds
                for user in guild.members
            )
        )

        channels = sum(
            len(guild.channels)
            for guild in self.bot.guilds
        )


        embed = discord.Embed(
            title="🌙 Iris Nova Stats",
            color=discord.Color.blue()
        )


        embed.add_field(
            name="🌐 Serwery",
            value=str(guilds),
            inline=True
        )

        embed.add_field(
            name="👥 Użytkownicy",
            value=str(users),
            inline=True
        )

        embed.add_field(
            name="📚 Kanały",
            value=str(channels),
            inline=True
        )

        embed.add_field(
            name="⚡ Ping",
            value=f"{round(self.bot.latency * 1000)} ms",
            inline=True
        )

        embed.add_field(
            name="⏱️ Uptime",
            value=get_uptime(),
            inline=True
        )


        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):

    await bot.add_cog(
        Stats(bot)
    )