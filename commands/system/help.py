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
            "⭐ Poziomy & XP": [],
            "🛡️ Moderacja": [],
            "⚙️ Konfiguracja": [],
            "📊 Informacje & AI": [],
            "👑 Owner": [],
            "🔧 Inne": [],
        }

        all_commands = set()

        # Pobieranie komend z walk_commands (dla hybrid_command oraz command)
        for cmd in self.bot.walk_commands():
            if not getattr(cmd, "hidden", False):
                all_commands.add(cmd.name)

        # Pobieranie komend z tree (dla app_commands)
        for cmd in self.bot.tree.get_commands():
            all_commands.add(cmd.name)

        for cmd_name in sorted(all_commands):

            if cmd_name == "help":
                continue

            name = f"`/{cmd_name}`"

            if cmd_name in {
                "play",
                "skip",
                "pause",
                "resume",
                "stop",
                "queue",
                "leave",
                "volume",
                "np",
                "nowplaying",
            }:
                categories["🎵 Muzyka"].append(name)

            elif cmd_name in {
                "rank",
                "leaderboard",
                "top",
                "set_level_channel",
                "add_xp",
                "remove_xp",
                "reset_lvl",
            }:
                categories["⭐ Poziomy & XP"].append(name)

            elif cmd_name in {
                "kick",
                "ban",
                "clear",
                "warn",
                "warnings",
                "temprole",
                "automod",
                "automod_config",
                "say",
                "ogloszenie",
                "embed",
                "sendmsg",
            }:
                categories["🛡️ Moderacja"].append(name)

            elif cmd_name in {
                "setup",
                "config",
                "modconfig",
                "settings",
                "welcome",
                "boost",
                "member_counter",
                "logs",
                "discord_logs",
                "ticket_setup",
                "tickets",
                "voice",
                "auto_voice",
                "reactionrole",
                "rr",
            }:
                categories["⚙️ Konfiguracja"].append(name)

            elif cmd_name in {
                "stats",
                "status",
                "userinfo",
                "serverinfo",
                "ping",
                "iris",
            }:
                categories["📊 Informacje & AI"].append(name)

            elif cmd_name in {
                "reload",
                "load",
                "unload",
                "eval",
                "sync",
            }:
                categories["👑 Owner"].append(name)

            else:
                categories["🔧 Inne"].append(name)

        embed = discord.Embed(
            title="🌙 Iris Nova",
            description="Lista wszystkich dostępnych komend:",
            color=EMBED_COLOR,
        )

        total_count = 0
        for title, cmds in categories.items():
            if cmds:
                unique_cmds = sorted(list(set(cmds)))
                total_count += len(unique_cmds)
                embed.add_field(
                    name=title,
                    value="\n".join(unique_cmds),
                    inline=False,
                )

        embed.set_footer(
            text=f"Łącznie komend: {total_count} • 🌙 Iris Nova"
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))