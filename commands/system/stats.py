import discord

from core.base_cog import BaseCog
from core.constants import EMBED_COLOR
from core.stats import get_uptime


class Stats(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)

    @discord.app_commands.command(
        name="stats",
        description="Pokazuje statystyki Iris."
    )
    async def stats(
        self,
        interaction: discord.Interaction,
    ):

        guilds = len(self.bot.guilds)

        users = len(
            {
                member.id
                for guild in self.bot.guilds
                for member in guild.members
            }
        )

        channels = sum(
            len(guild.channels)
            for guild in self.bot.guilds
        )

        embed = discord.Embed(
            title="📊 Statystyki Iris",
            color=EMBED_COLOR,
        )

        embed.add_field(
            name="🌐 Serwery",
            value=str(guilds),
        )

        embed.add_field(
            name="👥 Użytkownicy",
            value=str(users),
        )

        embed.add_field(
            name="📚 Kanały",
            value=str(channels),
        )

        embed.add_field(
            name="⚡ Ping",
            value=f"{round(self.bot.latency * 1000)} ms",
        )

        embed.add_field(
            name="⏱️ Uptime",
            value=get_uptime(),
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))