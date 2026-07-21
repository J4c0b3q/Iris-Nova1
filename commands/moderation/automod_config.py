import discord
from discord.ext import commands

from database.database import get_connection


class AutoModConfig(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



    # ==========================
    # AUTOMOD SETTINGS
    # ==========================


    @discord.app_commands.command(
        name="automod",
        description="Konfiguracja Iris AutoMod"
    )
    @discord.app_commands.describe(
        option="Opcja"
    )
    @discord.app_commands.choices(
        option=[

            discord.app_commands.Choice(
                name="Włącz antyspam",
                value="spam_on"
            ),

            discord.app_commands.Choice(
                name="Wyłącz antyspam",
                value="spam_off"
            ),

            discord.app_commands.Choice(
                name="Włącz linki",
                value="links_on"
            ),

            discord.app_commands.Choice(
                name="Wyłącz linki",
                value="links_off"
            ),

            discord.app_commands.Choice(
                name="Włącz caps",
                value="caps_on"
            ),

            discord.app_commands.Choice(
                name="Wyłącz caps",
                value="caps_off"
            )

        ]
    )
    @discord.app_commands.checks.has_permissions(
        administrator=True
    )
    async def automod(
        self,
        interaction: discord.Interaction,
        option: str
    ):


        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT OR IGNORE INTO automod_settings
            (guild_id)
            VALUES (?)
            """,
            (
                interaction.guild.id,
            )
        )


        updates = {

            "spam_on": ("anti_spam", 1),
            "spam_off": ("anti_spam", 0),

            "links_on": ("anti_links", 1),
            "links_off": ("anti_links", 0),

            "caps_on": ("anti_caps", 1),
            "caps_off": ("anti_caps", 0)

        }


        if option in updates:

            column, value = updates[option]


            cursor.execute(
                f"""
                UPDATE automod_settings
                SET {column}=?
                WHERE guild_id=?
                """,
                (
                    value,
                    interaction.guild.id
                )
            )


            conn.commit()


        conn.close()


        await interaction.response.send_message(
            f"✅ Ustawiono: `{option}`"
        )



    # ==========================
    # STATUS
    # ==========================


    @discord.app_commands.command(
        name="automod_status",
        description="Pokazuje ustawienia AutoModa"
    )
    async def automod_status(
        self,
        interaction: discord.Interaction
    ):


        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT anti_spam, anti_links, anti_caps
            FROM automod_settings
            WHERE guild_id=?
            """,
            (
                interaction.guild.id,
            )
        )


        data = cursor.fetchone()

        conn.close()


        if not data:

            data = (
                1,
                1,
                1
            )


        embed = discord.Embed(
            title="🛡️ Iris AutoMod",
            color=discord.Color.blue()
        )


        embed.add_field(
            name="🚨 Antyspam",
            value="🟢 ON" if data[0] else "🔴 OFF"
        )


        embed.add_field(
            name="🔗 Antylink",
            value="🟢 ON" if data[1] else "🔴 OFF"
        )


        embed.add_field(
            name="🔠 Antycaps",
            value="🟢 ON" if data[2] else "🔴 OFF"
        )


        await interaction.response.send_message(
            embed=embed
        )



    # ==========================
    # WHITELIST
    # ==========================


    @discord.app_commands.command(
        name="automod_whitelist",
        description="Zarządzanie wyjątkami AutoModa"
    )
    @discord.app_commands.describe(
        action="Akcja",
        member="Użytkownik",
        role="Rola"
    )
    @discord.app_commands.choices(
        action=[

            discord.app_commands.Choice(
                name="Dodaj użytkownika",
                value="add_user"
            ),

            discord.app_commands.Choice(
                name="Usuń użytkownika",
                value="remove_user"
            ),

            discord.app_commands.Choice(
                name="Dodaj rolę",
                value="add_role"
            ),

            discord.app_commands.Choice(
                name="Usuń rolę",
                value="remove_role"
            ),

            discord.app_commands.Choice(
                name="Lista wyjątków",
                value="list"
            )

        ]
    )
    @discord.app_commands.checks.has_permissions(
        administrator=True
    )
    async def automod_whitelist(
        self,
        interaction: discord.Interaction,
        action: str,
        member: discord.Member = None,
        role: discord.Role = None
    ):


        conn = get_connection()
        cursor = conn.cursor()



        if action == "add_user":

            cursor.execute(
                """
                INSERT INTO automod_whitelist
                (guild_id,user_id)
                VALUES (?,?)
                """,
                (
                    interaction.guild.id,
                    member.id
                )
            )


        elif action == "remove_user":

            cursor.execute(
                """
                DELETE FROM automod_whitelist
                WHERE guild_id=?
                AND user_id=?
                """,
                (
                    interaction.guild.id,
                    member.id
                )
            )


        elif action == "add_role":

            cursor.execute(
                """
                INSERT INTO automod_whitelist
                (guild_id,role_id)
                VALUES (?,?)
                """,
                (
                    interaction.guild.id,
                    role.id
                )
            )


        elif action == "remove_role":

            cursor.execute(
                """
                DELETE FROM automod_whitelist
                WHERE guild_id=?
                AND role_id=?
                """,
                (
                    interaction.guild.id,
                    role.id
                )
            )


        elif action == "list":

            cursor.execute(
                """
                SELECT user_id, role_id
                FROM automod_whitelist
                WHERE guild_id=?
                """,
                (
                    interaction.guild.id,
                )
            )


            data = cursor.fetchall()

            conn.close()


            text = ""

            for user_id, role_id in data:

                if user_id:
                    text += f"👤 <@{user_id}>\n"

                if role_id:
                    text += f"🎭 <@&{role_id}>\n"


            await interaction.response.send_message(
                text if text else "Brak wyjątków."
            )

            return



        conn.commit()
        conn.close()


        await interaction.response.send_message(
            "✅ Zmieniono whitelistę AutoModa"
        )

            # ==========================
    # BAD WORDS
    # ==========================


    @discord.app_commands.command(
        name="badword",
        description="Zarządzanie zakazanymi słowami"
    )
    @discord.app_commands.describe(
        action="Akcja",
        word="Słowo"
    )
    @discord.app_commands.choices(
        action=[

            discord.app_commands.Choice(
                name="Dodaj słowo",
                value="add"
            ),

            discord.app_commands.Choice(
                name="Usuń słowo",
                value="remove"
            ),

            discord.app_commands.Choice(
                name="Lista słów",
                value="list"
            )

        ]
    )
    @discord.app_commands.checks.has_permissions(
        administrator=True
    )
    async def badword(
        self,
        interaction: discord.Interaction,
        action: str,
        word: str = None
    ):


        conn = get_connection()
        cursor = conn.cursor()



        if action == "add":


            if not word:

                await interaction.response.send_message(
                    "❌ Podaj słowo.",
                    ephemeral=True
                )

                conn.close()
                return



            cursor.execute(
                """
                INSERT INTO bad_words
                (guild_id, word)
                VALUES (?,?)
                """,
                (
                    interaction.guild.id,
                    word.lower()
                )
            )


            conn.commit()


            await interaction.response.send_message(
                f"🚫 Dodano zakazane słowo: `{word}`"
            )



        elif action == "remove":


            cursor.execute(
                """
                DELETE FROM bad_words
                WHERE guild_id=?
                AND word=?
                """,
                (
                    interaction.guild.id,
                    word.lower()
                )
            )


            conn.commit()


            await interaction.response.send_message(
                f"✅ Usunięto: `{word}`"
            )



        elif action == "list":


            cursor.execute(
                """
                SELECT word
                FROM bad_words
                WHERE guild_id=?
                """,
                (
                    interaction.guild.id,
                )
            )


            data = cursor.fetchall()


            if data:

                text = "\n".join(
                    f"🚫 `{x[0]}`"
                    for x in data
                )

            else:

                text = "Brak zakazanych słów."


            await interaction.response.send_message(
                text
            )



        conn.close()

async def setup(bot):

    await bot.add_cog(
        AutoModConfig(bot)
    )