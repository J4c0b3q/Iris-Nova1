import discord
from discord.ext import commands


class SlashSystem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @discord.app_commands.command(
        name="ping",
        description="Sprawdza opóźnienie Iris"
    )
    async def ping(
        self,
        interaction: discord.Interaction
    ):

        latency = round(
            self.bot.latency * 1000
        )

        await interaction.response.send_message(
            f"🏓 Pong!\nOpóźnienie: `{latency}ms`"
        )


    @discord.app_commands.command(
        name="status",
        description="Pokazuje status Iris"
    )
    async def status(
        self,
        interaction: discord.Interaction
    ):

        guilds = len(self.bot.guilds)
        users = len(self.bot.users)

        embed = discord.Embed(
            title="🌙 Iris Nova Status",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🤖 Bot",
            value=str(self.bot.user),
            inline=False
        )

        embed.add_field(
            name="🌐 Serwery",
            value=str(guilds)
        )

        embed.add_field(
            name="👥 Użytkownicy",
            value=str(users)
        )


        await interaction.response.send_message(
            embed=embed
        )


    @discord.app_commands.command(
        name="help",
        description="Pokazuje listę komend Iris"
    )
    async def help(
        self,
        interaction: discord.Interaction
    ):

        commands_list = []

        for command in self.bot.tree.get_commands():

            commands_list.append(
                f"`/{command.name}`"
            )


        embed = discord.Embed(
            title="🌙 Iris Nova Pomoc",
            description="\n".join(commands_list),
            color=discord.Color.blue()
        )


        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(SlashSystem(bot))