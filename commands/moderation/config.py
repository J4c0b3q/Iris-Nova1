import discord
from discord.ext import commands

from core.config import PREFIX
from database.database import get_connection


class Config(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="setup",
        description="Konfiguracja kanałów logów, powitań oraz prefiksu dla serwera Iris"
    )
    @discord.app_commands.describe(
        option="Co chcesz skonfigurować",
        channel="Wybierz kanał tekstowy (dla kanałów logów/powitań)",
        new_prefix="Wpisz nowy prefix (jeśli wybrałeś opcję Prefiksu)"
    )
    @discord.app_commands.choices(
        option=[
            discord.app_commands.Choice(
                name="👥 Logi członków (dołączenia / opuszczenia)",
                value="member_logs"
            ),
            discord.app_commands.Choice(
                name="🛡️ Logi moderacji (bany / wyciszenia / kary)",
                value="moderation_logs"
            ),
            discord.app_commands.Choice(
                name="💬 Logi wiadomości (usunięcia / komendy)",
                value="message_logs"
            ),
            discord.app_commands.Choice(
                name="📝 Główny kanał logów (wszystkie 3 typy logów)",
                value="logs"
            ),
            discord.app_commands.Choice(
                name="👋 Kanał powitań",
                value="welcome"
            ),
            discord.app_commands.Choice(
                name="🎉 Kanał poziomów (level-up)",
                value="level_channel"
            ),
            discord.app_commands.Choice(
                name="🔧 Prefix komend (domyślnie /)",
                value="prefix"
            )
        ]
    )
    @discord.app_commands.checks.has_permissions(
        administrator=True
    )
    async def setup(
        self,
        interaction: discord.Interaction,
        option: str,
        channel: discord.TextChannel = None,
        new_prefix: str = None
    ):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO guilds
            (guild_id)
            VALUES (?)
            """,
            (
                interaction.guild.id,
            )
        )

        if option == "prefix":
            prefix_to_set = new_prefix or PREFIX
            cursor.execute(
                """
                UPDATE guilds
                SET prefix = ?
                WHERE guild_id = ?
                """,
                (
                    prefix_to_set,
                    interaction.guild.id
                )
            )
            message = f"✅ Prefix komend dla serwera został ustawiony na: `{prefix_to_set}`"

        else:
            if not channel:
                await interaction.response.send_message(
                    "❌ Musisz wybrać kanał tekstowy dla tej opcji!",
                    ephemeral=True
                )
                conn.close()
                return

            target_channel = channel

            if option == "logs":
                cursor.execute(
                    """
                    UPDATE guilds
                    SET log_channel = ?, member_log_channel = ?, moderation_log_channel = ?, message_log_channel = ?
                    WHERE guild_id = ?
                    """,
                    (
                        target_channel.id,
                        target_channel.id,
                        target_channel.id,
                        target_channel.id,
                        interaction.guild.id
                    )
                )
                message = f"✅ Wszystkie kanały logów ustawione na: {target_channel.mention}"

            elif option == "member_logs":
                cursor.execute(
                    """
                    UPDATE guilds
                    SET member_log_channel = ?
                    WHERE guild_id = ?
                    """,
                    (
                        target_channel.id,
                        interaction.guild.id
                    )
                )
                message = f"✅ Kanał logów członków ustawiony na: {target_channel.mention}"

            elif option == "moderation_logs":
                cursor.execute(
                    """
                    UPDATE guilds
                    SET moderation_log_channel = ?
                    WHERE guild_id = ?
                    """,
                    (
                        target_channel.id,
                        interaction.guild.id
                    )
                )
                message = f"✅ Kanał logów moderacji ustawiony na: {target_channel.mention}"

            elif option == "message_logs":
                cursor.execute(
                    """
                    UPDATE guilds
                    SET message_log_channel = ?
                    WHERE guild_id = ?
                    """,
                    (
                        target_channel.id,
                        interaction.guild.id
                    )
                )
                message = f"✅ Kanał logów wiadomości ustawiony na: {target_channel.mention}"

            elif option == "welcome":
                cursor.execute(
                    """
                    UPDATE guilds
                    SET welcome_channel = ?
                    WHERE guild_id = ?
                    """,
                    (
                        target_channel.id,
                        interaction.guild.id
                    )
                )
                message = f"✅ Kanał powitań ustawiony na: {target_channel.mention}"

            elif option == "level_channel":
                cursor.execute(
                    """
                    UPDATE guilds
                    SET level_channel = ?
                    WHERE guild_id = ?
                    """,
                    (
                        target_channel.id,
                        interaction.guild.id
                    )
                )
                message = f"✅ Kanał powiadomień o poziomach (level-up) ustawiony na: {target_channel.mention}"

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            message,
            ephemeral=True
        )

    @discord.app_commands.command(
        name="config",
        description="Pokazuje pełną konfigurację kanałów oraz ustawień Iris"
    )
    async def config(
        self,
        interaction: discord.Interaction
    ):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT log_channel, member_log_channel, moderation_log_channel, message_log_channel, welcome_channel, prefix, level_channel
            FROM guilds
            WHERE guild_id = ?
            """,
            (
                interaction.guild.id,
            )
        )

        data = cursor.fetchone()
        conn.close()

        if not data:
            await interaction.response.send_message(
                "⚠️ Ten serwer nie ma jeszcze skonfigurowanych kanałów. Użyj `/setup` aby je ustawić.",
                ephemeral=True
            )
            return

        def get_ch_mention(ch_id):
            if not ch_id:
                return "`Niekonsfigurowany`"
            ch = interaction.guild.get_channel(ch_id)
            return ch.mention if ch else f"<#{ch_id}>"

        member_log = get_ch_mention(data[1] or data[0])
        mod_log = get_ch_mention(data[2] or data[0])
        msg_log = get_ch_mention(data[3] or data[0])
        welcome_ch = get_ch_mention(data[4])
        prefix = data[5] or PREFIX
        level_ch = get_ch_mention(data[6])

        embed = discord.Embed(
            title="⚙️ Pełna Konfiguracja Iris Nova",
            description=f"Oto aktualny stan konfiguracji dla serwera **{interaction.guild.name}**:",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="👥 Logi Członków",
            value=member_log,
            inline=True
        )

        embed.add_field(
            name="🛡️ Logi Moderacji",
            value=mod_log,
            inline=True
        )

        embed.add_field(
            name="💬 Logi Wiadomości",
            value=msg_log,
            inline=True
        )

        embed.add_field(
            name="👋 Kanał Powitań",
            value=welcome_ch,
            inline=True
        )

        embed.add_field(
            name="🎉 Kanał Poziomów",
            value=level_ch,
            inline=True
        )

        embed.add_field(
            name="🔧 Prefix Komend",
            value=f"`{prefix}`",
            inline=True
        )

        embed.set_footer(
            text="🌙 Iris Nova • Użyj /setup aby zmienić te ustawienia"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Config(bot))