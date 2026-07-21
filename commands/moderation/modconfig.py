import discord
from discord.ext import commands

from core.database import get_connection


class ModConfig(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @discord.app_commands.command(
        name="modconfig",
        description="Konfiguracja automatycznych kar Iris"
    )
    @discord.app_commands.describe(
        option="Rodzaj kary",
        value="Ilość ostrzeżeń"
    )
    @discord.app_commands.choices(
        option=[

            discord.app_commands.Choice(
                name="🔇 Timeout",
                value="timeout"
            ),

            discord.app_commands.Choice(
                name="👢 Kick",
                value="kick"
            ),

            discord.app_commands.Choice(
                name="🔨 Ban",
                value="ban"
            )

        ]
    )
    @discord.app_commands.checks.has_permissions(
        administrator=True
    )
    async def modconfig(
        self,
        interaction: discord.Interaction,
        option: discord.app_commands.Choice[str] = None,
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


        # ustawianie wartości

        if option and value is not None:


            if value < 1:

                await interaction.response.send_message(
                    "❌ Liczba ostrzeżeń musi być większa od 0.",
                    ephemeral=True
                )

                conn.close()
                return



            option = option.value



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
                f"⚙️ Ustawiono **{option}** na **{value} ostrzeżeń**.",
                ephemeral=True
            )

            return



        # wyświetlanie konfiguracji


        cursor.execute(
            """
            SELECT
            timeout_warns,
            kick_warns,
            ban_warns

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
            description="Automatyczne kary za ostrzeżenia",
            color=discord.Color.blue()
        )


        embed.add_field(
            name="🔇 Timeout",
            value=f"`{data[0]}` ostrzeżeń",
            inline=False
        )


        embed.add_field(
            name="👢 Kick",
            value=f"`{data[1]}` ostrzeżeń",
            inline=False
        )


        embed.add_field(
            name="🔨 Ban",
            value=f"`{data[2]}` ostrzeżeń",
            inline=False
        )


        embed.set_footer(
            text="Iris Nova Moderation System"
        )


        await interaction.response.send_message(
            embed=embed
        )



async def setup(bot):

    await bot.add_cog(
        ModConfig(bot)
    )