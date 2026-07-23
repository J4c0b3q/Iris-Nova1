import discord
from discord.ext import commands

from core.config import PREFIX
from database.database import get_connection


class Config(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
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
    @commands.has_permissions(administrator=True)
    async def setup(
        self,
        ctx: commands.Context,
        option: str,
        channel: discord.TextChannel = None,
        new_prefix: str = None
    ):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO guilds
            (guild_id)
            VALUES (?)
            """,
            (
                ctx.guild.id,
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
                    ctx.guild.id
                )
            )
            message = f"✅ Prefix komend został zmieniony na: `{prefix_to_set}`"
        else:
            target_channel = channel or ctx.channel

            if option == "member_logs":
                cursor.execute(
                    """
                    UPDATE guilds
                    SET member_log_channel = ?
                    WHERE guild_id = ?
                    """,
                    (
                        target_channel.id,
                        ctx.guild.id
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
                        ctx.guild.id
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
                        ctx.guild.id
                    )
                )
                message = f"✅ Kanał logów wiadomości ustawiony na: {target_channel.mention}"

            elif option == "logs":
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
                        ctx.guild.id
                    )
                )
                message = f"✅ Główny kanał logów (wszystkie rodzaje) ustawiony na: {target_channel.mention}"

            elif option == "welcome":
                cursor.execute(
                    """
                    UPDATE guilds
                    SET welcome_channel = ?
                    WHERE guild_id = ?
                    """,
                    (
                        target_channel.id,
                        ctx.guild.id
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
                        ctx.guild.id
                    )
                )
                message = f"✅ Kanał powiadomień o poziomach (level-up) ustawiony na: {target_channel.mention}"

        conn.commit()
        conn.close()

        await ctx.send(
            message,
            ephemeral=True
        )

    @commands.hybrid_command(
        name="config",
        description="Pokazuje pełną konfigurację kanałów oraz ustawień Iris"
    )
    @commands.has_permissions(administrator=True)
    async def config(
        self,
        ctx: commands.Context
    ):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT log_channel, member_log_channel, moderation_log_channel, message_log_channel, welcome_channel, prefix, level_channel
            FROM guilds
            WHERE guild_id = ?
            """,
            (
                ctx.guild.id,
            )
        )

        data = cursor.fetchone()
        conn.close()

        if not data:
            await ctx.send(
                "⚠️ Ten serwer nie ma jeszcze skonfigurowanych kanałów. Użyj `/setup` aby je ustawić.",
                ephemeral=True
            )
            return

        def get_ch_mention(ch_id):
            if not ch_id:
                return "Nie ustawiono"
            ch = ctx.guild.get_channel(ch_id)
            return ch.mention if ch else "Nie odnaleziono kanału"

        main_log = get_ch_mention(data[0])
        member_log = get_ch_mention(data[1])
        mod_log = get_ch_mention(data[2])
        msg_log = get_ch_mention(data[3])
        welcome_ch = get_ch_mention(data[4])
        prefix = data[5] or PREFIX
        level_ch = get_ch_mention(data[6])

        embed = discord.Embed(
            title="⚙️ Pełna Konfiguracja Iris Nova",
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
            name="📝 Główny Log (Fallback)",
            value=main_log,
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
            text="🌙 Iris Nova • Użyj /setup aby zmienić ustawienia"
        )

        await ctx.send(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(
        Config(bot)
    )