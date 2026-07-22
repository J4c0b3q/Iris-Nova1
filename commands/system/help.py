import discord
from discord.ext import commands


class HelpCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="help",
        description="Wyświetla listę wszystkich dostępnych komend bota Iris Nova"
    )
    async def help_command(
        self,
        interaction: discord.Interaction
    ):

        categories = {
            "🎵 Muzyka": [],
            "⭐ Poziomy & XP": [],
            "🛡️ Moderacja": [],
            "⚙️ Konfiguracja": [],
            "📊 Informacje": [],
            "🛠️ Inne / Narzędzia": []
        }

        all_commands = self.bot.tree.get_commands()

        for command in all_commands:

            if command.name in ["reload", "load", "unload"]:
                continue

            name = f"`/{command.name}`"

            if command.name in {
                "play",
                "skip",
                "pause",
                "resume",
                "stop",
                "queue",
                "leave",
            }:
                categories["🎵 Muzyka"].append(name)

            elif command.name in {
                "rank",
                "leaderboard",
                "set_level_channel",
                "add_xp",
            }:
                categories["⭐ Poziomy & XP"].append(name)

            elif command.name in {
                "kick",
                "ban",
                "clear",
                "warn",
                "warnings",
            }:
                categories["🛡️ Moderacja"].append(name)

            elif command.name in {
                "setup",
                "config",
                "modconfig",
                "settings",
            }:
                categories["⚙️ Konfiguracja"].append(name)

            elif command.name in {
                "stats",
                "status",
            }:
                categories["📊 Informacje"].append(name)

            else:
                categories["🛠️ Inne / Narzędzia"].append(name)

        embed = discord.Embed(
            title="🌙 Iris Nova — Komendy Bota",
            description=(
                "Witaj! Oto spis dostępnych komend podzielony na kategorie.\n"
                "Użyj `/help [komenda]` lub `/setup` aby skonfigurować bota."
            ),
            color=discord.Color.purple()
        )

        for cat_name, cmd_list in categories.items():
            if cmd_list:
                embed.add_field(
                    name=cat_name,
                    value=" • ".join(cmd_list),
                    inline=False
                )

        embed.set_footer(
            text="🌙 Iris Nova • Twój wielofunkcyjny asystent Discord"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))