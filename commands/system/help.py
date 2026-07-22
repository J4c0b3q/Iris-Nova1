import discord

from core.base_cog import BaseCog
from core.constants import EMBED_COLOR


class Help(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)

    @discord.app_commands.command(
        name="help",
        description="Pokazuje wszystkie dostępne komendy."
    )
    async def help_command(
        self,
        interaction: discord.Interaction,
    ):

        categories = {
            "🎵 Muzyka": [],
            "🛡️ Moderacja": [],
            "⚙️ Konfiguracja": [],
            "📊 Informacje": [],
            "👑 Owner": [],
            "🤖 System": [],
            "🔧 Inne": [],
        }

        for command in self.bot.tree.get_commands():

            if command.name == "help":
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

            elif command.name in {
                "reload",
                "load",
                "unload",
            }:
                categories["👑 Owner"].append(name)

            elif command.name == "ping":
                categories["🤖 System"].append(name)

            else:
                categories["🔧 Inne"].append(name)

        embed = discord.Embed(
            title="🌙 Iris Nova",
            description="Lista dostępnych komend:",
            color=EMBED_COLOR,
        )

        for title, cmds in categories.items():
            if cmds:
                embed.add_field(
                    name=title,
                    value="\n".join(sorted(cmds)),
                    inline=False,
                )

        embed.set_footer(
            text=f"{len(self.bot.tree.get_commands())} komend"
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))