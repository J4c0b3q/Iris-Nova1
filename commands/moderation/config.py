import discord
from discord.ext import commands

from database.database import get_connection


class Config(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



    @discord.app_commands.command(
        name="setup",
        description="Konfiguracja Iris dla serwera"
    )
    @discord.app_commands.describe(
        option="Co chcesz skonfigurować"
    )
    @discord.app_commands.choices(
        option=[
            discord.app_commands.Choice(
                name="Kanał logów",
                value="logs"
            ),
            discord.app_commands.Choice(
                name="Kanał powitań",
                value="welcome"
            )
        ]
    )
    @discord.app_commands.checks.has_permissions(
        administrator=True
    )
    async def setup(
        self,
        interaction: discord.Interaction,
        option: str
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


        if option == "logs":

            cursor.execute(
                """
                UPDATE guilds
                SET log_channel = ?
                WHERE guild_id = ?
                """,
                (
                    interaction.channel.id,
                    interaction.guild.id
                )
            )


            message = (
                f"✅ Kanał logów ustawiony: "
                f"{interaction.channel.mention}"
            )


        elif option == "welcome":

            cursor.execute(
                """
                UPDATE guilds
                SET welcome_channel = ?
                WHERE guild_id = ?
                """,
                (
                    interaction.channel.id,
                    interaction.guild.id
                )
            )


            message = (
                f"✅ Kanał powitań ustawiony: "
                f"{interaction.channel.mention}"
            )


        conn.commit()
        conn.close()


        await interaction.response.send_message(
            message
        )



    @discord.app_commands.command(
        name="config",
        description="Pokazuje konfigurację Iris"
    )
    async def config(
        self,
        interaction: discord.Interaction
    ):


        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT log_channel, welcome_channel, prefix
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
                "⚠️ Ten serwer nie ma jeszcze konfiguracji."
            )

            return



        log_channel = (
            interaction.guild.get_channel(data[0])
            if data[0]
            else None
        )


        welcome_channel = (
            interaction.guild.get_channel(data[1])
            if data[1]
            else None
        )



        embed = discord.Embed(
            title="⚙️ Konfiguracja Iris",
            color=discord.Color.blue()
        )


        embed.add_field(
            name="📝 Logi",
            value=(
                log_channel.mention
                if log_channel
                else "Nie ustawiono"
            ),
            inline=False
        )


        embed.add_field(
            name="👋 Powitania",
            value=(
                welcome_channel.mention
                if welcome_channel
                else "Nie ustawiono"
            ),
            inline=False
        )


        embed.add_field(
            name="🔧 Prefix",
            value=data[2] or "!",
            inline=False
        )


        embed.set_footer(
            text="🌙 Iris Nova"
        )


        await interaction.response.send_message(
            embed=embed
        )



async def setup(bot):

    await bot.add_cog(
        Config(bot)
    )