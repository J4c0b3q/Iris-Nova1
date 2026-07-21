import discord
from discord.ext import commands


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="help")
    async def help_command(self, ctx):

        embed = discord.Embed(
            title="🌙 Iris Nova — Pomoc",
            description="Automatycznie wygenerowana lista komend:",
            color=discord.Color.blue()
        )


        commands_list = []


        for command in self.bot.commands:

            if command.hidden:
                continue

            if command.name == "help":
                continue

            commands_list.append(
                f"`!{command.name}`"
            )


        if commands_list:

            embed.add_field(
                name="🤖 Dostępne komendy",
                value="\n".join(commands_list),
                inline=False
            )

        else:

            embed.add_field(
                name="Brak komend",
                value="Nie znaleziono komend."
            )


        embed.set_footer(
            text=f"Iris Nova • {len(commands_list)} komend"
        )


        await ctx.send(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(Help(bot))