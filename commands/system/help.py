import discord
from discord.ext import commands


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @discord.app_commands.command(
        name="help",
        description="Pokazuje wszystkie dostępne komendy Iris"
    )
    async def help_command(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="🌙 Iris Nova — Pomoc",
            description="Lista dostępnych slash commands:",
            color=discord.Color.blue()
        )


        moderation = []
        configuration = []
        information = []
        owner = []
        system = []
        other = []


        commands_list = self.bot.tree.get_commands()


        for command in commands_list:

            name = f"`/{command.name}`"


            if command.name == "help":
                continue


            if command.name in [
                "kick",
                "ban",
                "clear",
                "warn",
                "warnings"
            ]:
                moderation.append(name)


            elif command.name in [
                "setup",
                "config",
                "modconfig"
            ]:
                configuration.append(name)


            elif command.name in [
                "stats",
                "status"
            ]:
                information.append(name)


            elif command.name in [
                "reload"
            ]:
                owner.append(name)


            elif command.name in [
                "ping"
            ]:
                system.append(name)


            else:
                other.append(name)



        if moderation:

            embed.add_field(
                name="🛡️ Moderacja",
                value="\n".join(moderation),
                inline=False
            )


        if configuration:

            embed.add_field(
                name="⚙️ Konfiguracja",
                value="\n".join(configuration),
                inline=False
            )


        if information:

            embed.add_field(
                name="📊 Informacje",
                value="\n".join(information),
                inline=False
            )


        if owner:

            embed.add_field(
                name="👑 Owner",
                value="\n".join(owner),
                inline=False
            )


        if system:

            embed.add_field(
                name="🤖 System",
                value="\n".join(system),
                inline=False
            )


        if other:

            embed.add_field(
                name="🔧 Inne",
                value="\n".join(other),
                inline=False
            )


        total = len(commands_list) - 1


        embed.set_footer(
            text=f"Iris Nova • {total} komend"
        )


        await interaction.response.send_message(
            embed=embed
        )



async def setup(bot):

    await bot.add_cog(
        Help(bot)
    )