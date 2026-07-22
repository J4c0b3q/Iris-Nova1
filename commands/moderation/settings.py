import discord
from discord import app_commands

from core.base_cog import BaseCog
from database.database import get_connection


class Settings(BaseCog, name="settings"):

    def __init__(self, bot):
        super().__init__(bot)

    # ==========================
    # LOGS
    # ==========================

    @app_commands.command(
        name="logs",
        description="Ustaw kanał logów."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def logs(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
    ):

        channel = channel or interaction.channel

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO guilds(guild_id)
            VALUES(?)
            """,
            (interaction.guild.id,)
        )

        cursor.execute(
            """
            UPDATE guilds
            SET log_channel = ?
            WHERE guild_id = ?
            """,
            (
                channel.id,
                interaction.guild.id,
            ),
        )

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"✅ Kanał logów ustawiono na {channel.mention}",
            ephemeral=True,
        )

    # ==========================
    # WELCOME
    # ==========================

    @app_commands.command(
        name="welcome",
        description="Ustaw kanał powitań."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
    ):

        channel = channel or interaction.channel

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO guilds(guild_id)
            VALUES(?)
            """,
            (interaction.guild.id,)
        )

        cursor.execute(
            """
            UPDATE guilds
            SET welcome_channel = ?
            WHERE guild_id = ?
            """,
            (
                channel.id,
                interaction.guild.id,
            ),
        )

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"✅ Kanał powitań ustawiono na {channel.mention}",
            ephemeral=True,
        )

    # ==========================
    # MODERATION
    # ==========================

    @app_commands.command(
        name="moderation",
        description="Konfiguracja automatycznych kar."
    )
    @app_commands.describe(
        option="Rodzaj kary",
        value="Liczba ostrzeżeń"
    )
    @app_commands.choices(
        option=[
            app_commands.Choice(name="Timeout", value="timeout"),
            app_commands.Choice(name="Kick", value="kick"),
            app_commands.Choice(name="Ban", value="ban"),
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def moderation(
        self,
        interaction: discord.Interaction,
        option: app_commands.Choice[str] | None = None,
        value: int | None = None,
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO moderation_settings(guild_id)
            VALUES(?)
            """,
            (interaction.guild.id,)
        )

        if option and value is not None:

            if value < 1:

                conn.close()

                await interaction.response.send_message(
                    "❌ Wartość musi być większa od 0.",
                    ephemeral=True,
                )

                return

            column = f"{option.value}_warns"

            cursor.execute(
                f"""
                UPDATE moderation_settings
                SET {column} = ?
                WHERE guild_id = ?
                """,
                (
                    value,
                    interaction.guild.id,
                ),
            )

            conn.commit()
            conn.close()

            await interaction.response.send_message(
                f"✅ {option.name}: **{value}**",
                ephemeral=True,
            )

            return

        cursor.execute(
            """
            SELECT
                timeout_warns,
                kick_warns,
                ban_warns
            FROM moderation_settings
            WHERE guild_id = ?
            """,
            (interaction.guild.id,),
        )

        data = cursor.fetchone()

        conn.close()

        if not data:
            data = (3, 5, 10)

        embed = discord.Embed(
            title="🛡️ Moderacja",
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="Timeout",
            value=data[0],
        )

        embed.add_field(
            name="Kick",
            value=data[1],
        )

        embed.add_field(
            name="Ban",
            value=data[2],
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    # ==========================
    # SHOW
    # ==========================

    @app_commands.command(
        name="show",
        description="Pokaż konfigurację."
    )
    async def show(
        self,
        interaction: discord.Interaction,
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                log_channel,
                welcome_channel,
                prefix
            FROM guilds
            WHERE guild_id = ?
            """,
            (interaction.guild.id,),
        )

        data = cursor.fetchone()

        conn.close()

        if not data:

            await interaction.response.send_message(
                "⚠️ Brak konfiguracji.",
                ephemeral=True,
            )

            return

        embed = discord.Embed(
            title="⚙️ Konfiguracja",
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="Logi",
            value=f"<#{data[0]}>" if data[0] else "Nie ustawiono",
            inline=False,
        )

        embed.add_field(
            name="Powitania",
            value=f"<#{data[1]}>" if data[1] else "Nie ustawiono",
            inline=False,
        )

        embed.add_field(
            name="Prefix",
            value=data[2] or "!",
            inline=False,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Settings(bot))