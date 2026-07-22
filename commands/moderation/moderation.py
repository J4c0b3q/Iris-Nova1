import datetime
import re
import discord
from discord.ext import commands, tasks

from core.base_cog import BaseCog
from database.database import get_connection


def parse_duration(time_str: str) -> int:
    """Konwertuje napis z czasem (np. '10m', '2h', '3d', '30s') na sekundy."""
    time_str = time_str.strip().lower()
    match = re.match(r"^(\d+)\s*([smhd])$", time_str)
    if not match:
        if time_str.isdigit():
            return int(time_str) * 60
        return 0
    val, unit = match.groups()
    val = int(val)
    if unit == 's':
        return val
    elif unit == 'm':
        return val * 60
    elif unit == 'h':
        return val * 3600
    elif unit == 'd':
        return val * 86400
    return 0


class Moderation(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.check_temp_roles.start()

    def cog_unload(self):
        self.check_temp_roles.cancel()

    @tasks.loop(seconds=30)
    async def check_temp_roles(self):
        """Sprawdza i odbiera wygasłe tymczasowe role."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, guild_id, user_id, role_id FROM temp_roles WHERE expires_at <= datetime('now')"
            )
            expired = cursor.fetchall()

            for row_id, guild_id, user_id, role_id in expired:
                guild = self.bot.get_guild(guild_id)
                if guild:
                    role = guild.get_role(role_id)
                    member = guild.get_member(user_id)
                    if not member:
                        try:
                            member = await guild.fetch_member(user_id)
                        except Exception:
                            member = None

                    if member and role and role in member.roles:
                        try:
                            await member.remove_roles(role, reason="Wygaśnięcie tymczasowej roli")
                            self.logger.info(f"Odebrano wygasłą rolę {role.name} użytkownikowi {member}")
                        except Exception as e:
                            self.logger.error(f"Nie udało się odebrać roli {role_id} użytkownikowi {user_id}: {e}")

                cursor.execute("DELETE FROM temp_roles WHERE id = ?", (row_id,))

            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Błąd pętli check_temp_roles: {e}")

    @check_temp_roles.before_loop
    async def before_check_roles(self):
        await self.bot.wait_until_ready()

    @discord.app_commands.command(
        name="kick",
        description="Wyrzuca użytkownika z serwera"
    )
    @discord.app_commands.describe(
        member="Użytkownik do wyrzucenia",
        reason="Powód wyrzucenia"
    )
    @discord.app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Brak powodu"
    ):
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                "❌ Nie możesz wyrzucić użytkownika z rolą równą lub wyższą od Twojej!",
                ephemeral=True
            )
            return

        try:
            await member.kick(reason=f"Wyrzucony przez {interaction.user}: {reason}")

            embed = discord.Embed(
                title="👢 Wyrzucono Użytkownika",
                color=discord.Color.orange()
            )
            embed.add_field(name="Użytkownik", value=f"{member.mention} ({member})", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            embed.add_field(name="Powód", value=reason, inline=False)
            embed.set_footer(text="🌙 Iris Nova • Moderacja")

            await interaction.response.send_message(embed=embed)
            self.logger.info(f"{interaction.user} wyrzucił {member} za: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Bot nie posiada uprawnień do wyrzucenia tego użytkownika (sprawdź hierarchię ról)!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Wystąpił błąd podczas wyrzucania: {e}",
                ephemeral=True
            )

    @discord.app_commands.command(
        name="ban",
        description="Baniuje użytkownika z serwera"
    )
    @discord.app_commands.describe(
        member="Użytkownik do zbanowania",
        reason="Powód bana",
        delete_days="Liczba dni wiadomości do usunięcia (0-7)"
    )
    @discord.app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Brak powodu",
        delete_days: int = 0
    ):
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                "❌ Nie możesz zbanować użytkownika z rolą równą lub wyższą od Twojej!",
                ephemeral=True
            )
            return

        delete_days = max(0, min(7, delete_days))

        try:
            await member.ban(
                reason=f"Zbanowany przez {interaction.user}: {reason}",
                delete_message_days=delete_days
            )

            embed = discord.Embed(
                title="🔨 Zbanowano Użytkownika",
                color=discord.Color.red()
            )
            embed.add_field(name="Użytkownik", value=f"{member.mention} ({member})", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            embed.add_field(name="Powód", value=reason, inline=False)
            if delete_days > 0:
                embed.add_field(name="Usunięte wiadomości z", value=f"{delete_days} dni", inline=False)
            embed.set_footer(text="🌙 Iris Nova • Moderacja")

            await interaction.response.send_message(embed=embed)
            self.logger.info(f"{interaction.user} zbanował {member} za: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Bot nie posiada uprawnień do zbanowania tego użytkownika (sprawdź hierarchię ról)!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Wystąpił błąd podczas banowania: {e}",
                ephemeral=True
            )

    @discord.app_commands.command(
        name="temprole",
        description="Nadaje użytkownikowi rolę na określony czas (np. 10m, 2h, 3d)"
    )
    @discord.app_commands.describe(
        member="Użytkownik",
        role="Rola do nadania",
        duration="Czas trwania, np. 30s, 10m, 2h, 3d",
        reason="Powód nadania roli"
    )
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def temprole(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        duration: str,
        reason: str = "Brak powodu"
    ):
        seconds = parse_duration(duration)
        if seconds <= 0:
            await interaction.response.send_message(
                "❌ Nieprawidłowy format czasu! Przykłady: `30s`, `10m`, `2h`, `3d`.",
                ephemeral=True
            )
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ Rola znajduje się na samej górze lub powyżej roli bota w hierarchii!",
                ephemeral=True
            )
            return

        try:
            await member.add_roles(role, reason=f"Tymczasowa rola od {interaction.user} ({duration}): {reason}")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO temp_roles (guild_id, user_id, role_id, expires_at)
                VALUES (?, ?, ?, datetime('now', '+' || ? || ' seconds'))
                """,
                (interaction.guild.id, member.id, role.id, seconds)
            )
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title="⏱️ Nadano Tymczasową Rolę",
                color=discord.Color.blue()
            )
            embed.add_field(name="Użytkownik", value=member.mention, inline=False)
            embed.add_field(name="Rola", value=role.mention, inline=False)
            embed.add_field(name="Czas trwania", value=duration, inline=False)
            embed.add_field(name="Powód", value=reason, inline=False)
            embed.set_footer(text="🌙 Iris Nova • Moderacja")

            await interaction.response.send_message(embed=embed)
            self.logger.info(f"{interaction.user} nadał rolę {role.name} użytkownikowi {member} na {duration}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Bot nie posiada uprawnień do nadania tej roli!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Wystąpił błąd: {e}",
                ephemeral=True
            )

    @discord.app_commands.command(
        name="clear",
        description="Usuwa określoną liczbę wiadomości z kanału"
    )
    @discord.app_commands.describe(
        amount="Liczba wiadomości do usunięcia (1-100)",
        member="Opcjonalnie: usuwaj tylko wiadomości od tej osoby"
    )
    @discord.app_commands.checks.has_permissions(manage_messages=True)
    async def clear(
        self,
        interaction: discord.Interaction,
        amount: int,
        member: discord.Member = None
    ):
        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                "❌ Podaj liczbę wiadomości w zakresie od 1 do 100!",
                ephemeral=True
            )
            return

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        def check(msg: discord.Message):
            if member:
                return msg.author.id == member.id
            return True

        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            count = len(deleted)
            msg = f"🧹 Pomyślnie usunięto **{count}** wiadomości"
            if member:
                msg += f" od {member.mention}"
            msg += "."
            await interaction.followup.send(msg, ephemeral=True)
            self.logger.info(f"{interaction.user} usunął {count} wiadomości na kanale {interaction.channel}")
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Bot nie posiada uprawnienia **Zarządzanie Wiadomościami (Manage Messages)**!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Wystąpił błąd podczas usuwania wiadomości: {e}",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Moderation(bot))