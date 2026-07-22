import discord
from discord.ext import commands, tasks
import datetime

from database.database import get_connection


def clean_expired_warns():
    """Usuwa z bazy danych wszystkie ostrzeżenia starsze niż 3 dni."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM warnings WHERE date < datetime('now', '-3 days')")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    except Exception:
        return 0


class Warnings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.auto_clean_warns.start()

    def cog_unload(self):
        self.auto_clean_warns.cancel()

    @tasks.loop(minutes=30)
    async def auto_clean_warns(self):
        deleted = clean_expired_warns()
        if deleted > 0 and hasattr(self.bot, "logger"):
            self.bot.logger.info(f"🧹 Automatycznie usunięto {deleted} wygasłych ostrzeżeń (starszych niż 3 dni).")

    @auto_clean_warns.before_loop
    async def before_auto_clean(self):
        await self.bot.wait_until_ready()

    @discord.app_commands.command(
        name="warn",
        description="Nadaj ostrzeżenie użytkownikowi"
    )
    @discord.app_commands.checks.has_permissions(kick_members=True)
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Brak powodu"
    ):
        clean_expired_warns()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
            VALUES (?, ?, ?, ?)
            """,
            (interaction.guild.id, member.id, interaction.user.id, reason)
        )

        conn.commit()

        cursor.execute(
            """
            SELECT COUNT(*) FROM warnings
            WHERE guild_id = ? AND user_id = ?
            """,
            (interaction.guild.id, member.id)
        )

        warn_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT timeout_warns, kick_warns, ban_warns
            FROM moderation_settings
            WHERE guild_id = ?
            """,
            (interaction.guild.id,)
        )

        settings = cursor.fetchone()

        conn.close()

        embed = discord.Embed(
            title="⚠️ Ostrzeżenie",
            description=f"Użytkownik {member.mention} otrzymał ostrzeżenie.",
            color=discord.Color.orange()
        )

        embed.add_field(name="Powód", value=reason, inline=False)
        embed.add_field(name="Liczba ostrzeżeń", value=str(warn_count), inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)

        await interaction.response.send_message(embed=embed)

        if settings:

            timeout_limit, kick_limit, ban_limit = settings

            if warn_count >= ban_limit:

                try:
                    await member.ban(reason="Przekroczono limit ostrzeżeń (BAN)")
                    await interaction.channel.send(
                        f"🔨 Użytkownik {member.mention} został automatycznie zbanowany."
                    )
                except Exception:
                    pass

            elif warn_count >= kick_limit:

                try:
                    await member.kick(reason="Przekroczono limit ostrzeżeń (KICK)")
                    await interaction.channel.send(
                        f"🥾 Użytkownik {member.mention} został automatycznie wyrzucony."
                    )
                except Exception:
                    pass

            elif warn_count >= timeout_limit:

                try:
                    duration = datetime.timedelta(minutes=10)
                    await member.timeout(duration, reason="Przekroczono limit ostrzeżeń (TIMEOUT)")
                    await interaction.channel.send(
                        f"⏰ Użytkownik {member.mention} otrzymał wyciszenie na 10 minut."
                    )
                except Exception:
                    pass

    @discord.app_commands.command(
        name="warns",
        description="Sprawdź ostrzeżenia użytkownika"
    )
    async def warns(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        clean_expired_warns()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, reason, date FROM warnings
            WHERE guild_id = ? AND user_id = ?
            """,
            (interaction.guild.id, member.id)
        )

        rows = cursor.fetchall()

        conn.close()

        if not rows:
            await interaction.response.send_message(
                f"Użytkownik {member.mention} nie posiada żadnych aktywnych ostrzeżeń.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"⚠️ Ostrzeżenia {member.display_name}",
            color=discord.Color.red()
        )

        for row in rows:
            warn_id, reason, date = row
            embed.add_field(
                name=f"ID: {warn_id}",
                value=f"Powód: {reason}\nData: {date}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(
        name="unwarn",
        description="Usuń ostrzeżenie użytkownikowi"
    )
    @discord.app_commands.checks.has_permissions(kick_members=True)
    async def unwarn(
        self,
        interaction: discord.Interaction,
        warn_id: int
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM warnings
            WHERE id = ? AND guild_id = ?
            """,
            (warn_id, interaction.guild.id)
        )

        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        if deleted == 0:
            await interaction.response.send_message(
                "Nie znaleziono ostrzeżenia o podanym ID.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Usunięto ostrzeżenie o ID **{warn_id}**."
            )

    @discord.app_commands.command(
        name="clearwarns",
        description="Wyczyść wszystkie ostrzeżenia użytkownika"
    )
    @discord.app_commands.checks.has_permissions(kick_members=True)
    async def clearwarns(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM warnings
            WHERE guild_id = ? AND user_id = ?
            """,
            (interaction.guild.id, member.id)
        )

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"Wyczyszczono wszystkie ostrzeżenia dla {member.mention}."
        )


async def setup(bot):
    await bot.add_cog(Warnings(bot))