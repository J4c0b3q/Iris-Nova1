import discord
from discord.ext import commands

from core.base_cog import BaseCog
from core.constants import EMBED_COLOR


class Basic(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.hybrid_command(
        name="ping",
        description="Pokazuje aktualne opóźnienie bota."
    )
    async def ping(self, ctx: commands.Context):

        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Opóźnienie: **{latency} ms**",
            color=EMBED_COLOR,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Basic(bot))