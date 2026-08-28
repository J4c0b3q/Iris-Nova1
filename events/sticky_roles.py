import discord
from discord.ext import commands
from database.database import get_connection
from core.logger import get_logger

logger = get_logger("StickyRoles")


class StickyRoles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Filtrujemy domyślne role, zarządzane (np. od botów, boosterów) oraz @everyone
        roles_to_save = [
            role.id
            for role in member.roles
            if not role.is_default() and not role.managed
        ]

        if not roles_to_save:
            # Użytkownik nie miał żadnych ról do zapisania, usuwamy ewentualny stary wpis
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM sticky_roles WHERE guild_id = ? AND user_id = ?",
                    (member.guild.id, member.id)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Błąd przy usuwaniu pustego wpisu sticky_roles dla {member}: {e}")
            return

        roles_str = ",".join(map(str, roles_to_save))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO sticky_roles (guild_id, user_id, roles)
                VALUES (?, ?, ?)
                """,
                (member.guild.id, member.id, roles_str)
            )
            conn.commit()
            conn.close()
            logger.info(f"Zapisano role dla użytkownika {member} ({member.id}) na serwerze {member.guild.name}: {roles_to_save}")
        except Exception as e:
            logger.error(f"Nie udało się zapisać ról dla użytkownika {member}: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT roles FROM sticky_roles WHERE guild_id = ? AND user_id = ?",
                (guild.id, member.id)
            )
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            logger.error(f"Nie udało się pobrać zapisanych ról dla {member}: {e}")
            return

        if not row or not row[0]:
            return

        roles_str = row[0]
        role_ids = [int(r_id) for r_id in roles_str.split(",") if r_id.strip()]

        roles_to_add = []
        for r_id in role_ids:
            role = guild.get_role(r_id)
            if role and not role.managed:
                roles_to_add.append(role)

        if not roles_to_add:
            return

        # Sprawdzamy uprawnienia bota do nadawania ról
        bot_member = guild.me
        if not bot_member.guild_permissions.manage_roles:
            logger.warning(f"Brak uprawnień 'Zarządzanie rolami' na serwerze {guild.name}, nie można przywrócić ról dla {member}.")
            return

        # Filtrujemy tylko role, które są poniżej najwyższej roli bota
        bot_highest_role = bot_member.top_role
        roles_addable = [
            role
            for role in roles_to_add
            if role < bot_highest_role
        ]

        if not roles_addable:
            logger.warning(f"Zapisane role dla {member} są wyższe niż najwyższa rola bota. Pomijam przywracanie.")
            return

        try:
            await member.add_roles(*roles_addable, reason="Automatyczne przywracanie ról po dołączeniu (Sticky Roles)")
            logger.info(f"Pomyślnie przywrócono role dla {member} ({member.id}): {[r.name for r in roles_addable]}")

            # Po pomyślnym nadaniu ról, usuwamy wpis z bazy, by nie dublować starych danych
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM sticky_roles WHERE guild_id = ? AND user_id = ?",
                (guild.id, member.id)
            )
            conn.commit()
            conn.close()

        except discord.Forbidden:
            logger.error(f"Brak uprawnień Discord (Forbidden) do przywrócenia ról dla {member}.")
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas dodawania ról dla {member}: {e}")


async def setup(bot):
    await bot.add_cog(StickyRoles(bot))