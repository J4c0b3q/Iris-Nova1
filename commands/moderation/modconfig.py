import discord
from discord.ext import commands

from core.database import get_connection


class ModConfig(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



    @discord.app_commands.command(
        name="modconfig",
        description="Konfiguruje automatyczne kary za ostrzeżenia"
    )
    @discord.app_commands.describe(
        option="Opcja: timeout, kick lub ban",
        value="Ilość ostrzeżeń"
    )
    @discord.app_commands.checks.has_permissions(
        administrator=True
    )
    async def modconfig(
        self,
        interaction: discord.Interaction,
        option: str = None,
        value: int = None
    ):


        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT OR IGNORE INTO moderation_settings
            (guild_id)
            VALUES (?)
            """,
            (
                interaction.guild.id,
            )
        )


        if option and value is not None:


            if option not in [
                "timeout",
                "kick",
                "ban"
            ]:

                await interaction.response.send_message(
                    "❌ Dostępne opcje: timeout, kick, ban",
                    ephemeral=True
                )

                conn.close()
                return



            if option == "timeout":

                cursor.execute(
                    """
                    UPDATE moderation_settings
                    SET timeout_warns = ?
                    WHERE guild_id = ?
                    """,
                    (
                        value,
                        interaction.guild.id
                    )
                )


            elif option == "kick":

                cursor.execute(
                    """
                    UPDATE moderation_settings
                    SET kick_warns = ?
                    WHERE guild_id = ?
                    """,
                    (
                        value,
                        interaction.guild.id
                    )
                )


            elif option == "ban":

                cursor.execute(
                    """
                    UPDATE moderation_settings
                    SET ban_warns = ?
                    WHERE guild_id = ?
                    """,
                    (
                        value,
                        interaction.guild.id
                    )
                )


            conn.commit()
            conn.close()


            await interaction.response.send_message(
                f"⚙️ Ustawiono `{option}` na `{value}` ostrzeżeń."
            )

            return



        cursor.execute(
            """
            SELECT timeout_warns, kick_warns, ban_warns
            FROM moderation_settings
            WHERE guild_id = ?
            """,
            (
                interaction.guild.id,
            )
        )


        data = cursor.fetchone()

        conn.close()


        if not data:

            data = (
                3,
                5,
                10
            )



        embed = discord.Embed(
            title="🛡️ Iris Nova — Moderacja",
            color=discord.Color.blue()
        )


        embed.add_field(
            name="🔇 Timeout",
            value=f"{data[0]} ostrzeżeń",
            inline=False
        )


        embed.add_field(
            name="👢 Kick",
            value=f"{data[1]} ostrzeżeń",
            inline=False
        )


        embed.add_field(
            name="🔨 Ban",
            value=f"{data[2]} ostrzeżeń",
            inline=False
        )


        await interaction.response.send_message(
            embed=embed
        )



async def setup(bot):

    await bot.add_cog(
        ModConfig(bot)
    )