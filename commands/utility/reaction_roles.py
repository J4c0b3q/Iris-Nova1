import discord
from discord.ext import commands
from discord import app_commands

from core.base_cog import BaseCog
from core.constants import EMBED_COLOR
from core.logger import get_logger
from database.database import get_connection

logger = get_logger("ReactionRoles")


def is_emoji_match(saved_emoji: str, payload_emoji: discord.PartialEmoji) -> bool:
    saved = saved_emoji.strip()
    payload_str = str(payload_emoji).strip()
    if saved == payload_str:
        return True
    if payload_emoji.is_custom_emoji():
        if saved == payload_emoji.name or saved == str(payload_emoji.id):
            return True
        if str(payload_emoji.id) in saved or payload_emoji.name in saved:
            return True
    return False


class ReactionRoles(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.hybrid_group(
        name="reactionrole",
        aliases=["rr"],
        description="Zarządzanie rolami za reakcje"
    )
    @commands.has_permissions(manage_roles=True)
    async def reactionrole(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="⭐ System Ról za Reakcje (Reaction Roles)",
                description=(
                    "Dostępne podkomendy:\n"
                    "• `/reactionrole add <message_id> <emoji> <role> [channel]` - Dodaje rolę za reakcję\n"
                    "• `/reactionrole remove <message_id> <emoji> [channel]` - Usuwa rolę za reakcję\n"
                    "• `/reactionrole list` - Wyświetla listę aktywnych ról za reakcje\n"
                    "• `/reactionrole clear <message_id> [channel]` - Usuwa wszystkie reakcje z wiadomości\n"
                    "• `/reactionrole embed <tytul> <opis> [channel]` - Tworzy nową wiadomość z opisem ról"
                ),
                color=EMBED_COLOR
            )
            embed.set_footer(text=f"🌙 {ctx.guild.name}" if ctx.guild else "🌙 Iris Nova")
            await ctx.send(embed=embed)

    @reactionrole.command(
        name="add",
        aliases=["dodaj"],
        description="Dodaje rolę za reakcję do wybranej wiadomości"
    )
    @app_commands.describe(
        message_id="ID wiadomości, do której ma zostać dodana reakcja",
        emoji="Emotka (np. ⭐ lub własna emotka)",
        role="Rola, która ma zostać przyznana po kliknięciu reakcji",
        channel="Kanał, na którym znajduje się wiadomość (opcjonalnie)"
    )
    @commands.has_permissions(manage_roles=True)
    async def rr_add(
        self,
        ctx: commands.Context,
        message_id: str,
        emoji: str,
        role: discord.Role,
        channel: discord.TextChannel = None
    ):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        target_channel = channel or ctx.channel

        try:
            msg_id_int = int(message_id.strip())
        except ValueError:
            await ctx.send("❌ Podano nieprawidłowe ID wiadomości (musi być liczbą).", ephemeral=True)
            return

        try:
            target_message = await target_channel.fetch_message(msg_id_int)
        except discord.NotFound:
            await ctx.send(f"❌ Nie znaleziono wiadomości o ID `{message_id}` na kanale {target_channel.mention}.", ephemeral=True)
            return
        except discord.Forbidden:
            await ctx.send("❌ Bot nie ma dostępu do czytania wiadomości na wskazanym kanale.", ephemeral=True)
            return
        except Exception as e:
            await ctx.send(f"❌ Błąd podczas pobierania wiadomości: {e}", ephemeral=True)
            return

        # Sprawdzenie czy rola bota jest wyższa niż rola docelowa
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send(f"❌ Rola {role.mention} znajduje się wyżej lub na tym samym poziomie co najwyższa rola bota. Przesuń rolę bota wyżej w ustawieniach serwera.", ephemeral=True)
            return

        clean_emoji = emoji.strip()

        # Dodanie reakcji do wiadomości przez bota
        try:
            await target_message.add_reaction(clean_emoji)
        except discord.HTTPException:
            await ctx.send(f"❌ Nie udało się dodać reakcji `{clean_emoji}`. Upewnij się, że emotka jest poprawna i bot ma do niej dostęp.", ephemeral=True)
            return

        # Zapis do bazy danych
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO reaction_roles (guild_id, channel_id, message_id, emoji, role_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ctx.guild.id, target_channel.id, target_message.id, clean_emoji, role.id)
        )
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="✅ Pomyślnie dodano rolę za reakcję",
            description=(
                f"• **Wiadomość ID:** `{target_message.id}`\n"
                f"• **Kanał:** {target_channel.mention}\n"
                f"• **Emotka:** {clean_emoji}\n"
                f"• **Rola:** {role.mention}"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"🌙 {ctx.guild.name}")
        await ctx.send(embed=embed)

    @reactionrole.command(
        name="remove",
        aliases=["usun"],
        description="Usuwa rolę za reakcję z wiadomości"
    )
    @app_commands.describe(
        message_id="ID wiadomości",
        emoji="Emotka przypisana do roli",
        channel="Kanał, na którym znajduje się wiadomość (opcjonalnie)"
    )
    @commands.has_permissions(manage_roles=True)
    async def rr_remove(
        self,
        ctx: commands.Context,
        message_id: str,
        emoji: str,
        channel: discord.TextChannel = None
    ):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        try:
            msg_id_int = int(message_id.strip())
        except ValueError:
            await ctx.send("❌ Podano nieprawidłowe ID wiadomości.", ephemeral=True)
            return

        clean_emoji = emoji.strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM reaction_roles
            WHERE guild_id = ? AND message_id = ? AND emoji = ?
            """,
            (ctx.guild.id, msg_id_int, clean_emoji)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted == 0:
            await ctx.send(f"❌ Nie znaleziono roli za reakcję dla wiadomości `{message_id}` z emotką `{clean_emoji}`.", ephemeral=True)
            return

        target_channel = channel or ctx.channel
        try:
            target_message = await target_channel.fetch_message(msg_id_int)
            await target_message.remove_reaction(clean_emoji, ctx.guild.me)
        except Exception:
            pass

        embed = discord.Embed(
            title="✅ Usunięto rolę za reakcję",
            description=f"Usunięto powiązanie emotki {clean_emoji} z wiadomości `{message_id}`.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"🌙 {ctx.guild.name}")
        await ctx.send(embed=embed)

    @reactionrole.command(
        name="list",
        aliases=["lista"],
        description="Wyświetla listę wszystkich aktywnych ról za reakcje na serwerze"
    )
    @commands.has_permissions(manage_roles=True)
    async def rr_list(self, ctx: commands.Context):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT channel_id, message_id, emoji, role_id
            FROM reaction_roles
            WHERE guild_id = ?
            """,
            (ctx.guild.id,)
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await ctx.send("ℹ️ Na tym serwerze nie ma jeszcze skonfigurowanych ról za reakcje.", ephemeral=True)
            return

        embed = discord.Embed(
            title="⭐ Lista ról za reakcje (Reaction Roles)",
            color=EMBED_COLOR
        )

        lines = []
        for ch_id, msg_id, emoji, role_id in rows:
            channel = ctx.guild.get_channel(ch_id)
            role = ctx.guild.get_role(role_id)
            ch_mention = channel.mention if channel else f"<#{ch_id}>"
            role_mention = role.mention if role else f"<@&{role_id}>"

            lines.append(f"• Kanał: {ch_mention} | Msg ID: `{msg_id}`\n  Reakcja: {emoji} ➔ Rola: {role_mention}")

        embed.description = "\n\n".join(lines)
        embed.set_footer(text=f"Łącznie powiązań: {len(rows)} • 🌙 {ctx.guild.name}")

        await ctx.send(embed=embed)

    @reactionrole.command(
        name="clear",
        aliases=["wyczysc"],
        description="Usuwa wszystkie role za reakcje powiązane z daną wiadomością"
    )
    @app_commands.describe(
        message_id="ID wiadomości"
    )
    @commands.has_permissions(manage_roles=True)
    async def rr_clear(self, ctx: commands.Context, message_id: str):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        try:
            msg_id_int = int(message_id.strip())
        except ValueError:
            await ctx.send("❌ Podano nieprawidłowe ID wiadomości.", ephemeral=True)
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM reaction_roles
            WHERE guild_id = ? AND message_id = ?
            """,
            (ctx.guild.id, msg_id_int)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted == 0:
            await ctx.send(f"❌ Brak ról za reakcje powiązanych z wiadomością `{message_id}`.", ephemeral=True)
            return

        await ctx.send(f"✅ Usunięto wszystkie ({deleted}) role za reakcje z wiadomości `{message_id}`.")

    @reactionrole.command(
        name="embed",
        description="Tworzy estetyczny Embed na wybranym kanale (np. 'Wybierz swoje role')"
    )
    @app_commands.describe(
        tytul="Tytuł wiadomości z rolami",
        opis="Opis wiadomości (użyj \\n aby zrobić nową linię)",
        kanal="Kanał, na którym ma zostać wysłany Embed (opcjonalnie)",
        kolor="Kolor ramki (np. #ff0000, red, gold, blue, purple)"
    )
    @commands.has_permissions(manage_roles=True)
    async def rr_embed(
        self,
        ctx: commands.Context,
        tytul: str,
        opis: str,
        kanal: discord.TextChannel = None,
        kolor: str = None
    ):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        target_channel = kanal or ctx.channel
        formatted_desc = opis.replace("\\n", "\n")

        embed_color = EMBED_COLOR
        if kolor:
            try:
                if kolor.startswith("#"):
                    embed_color = discord.Color(int(kolor[1:], 16))
                else:
                    embed_color = discord.Color(int(kolor, 16))
            except Exception:
                embed_color = EMBED_COLOR

        embed = discord.Embed(
            title=tytul,
            description=formatted_desc,
            color=embed_color
        )
        embed.set_footer(text=f"🌙 {ctx.guild.name}")

        msg = await target_channel.send(embed=embed)

        info_msg = (
            f"✅ Pomyślnie wysłano wiadomość z rolami na kanał {target_channel.mention}!\n"
            f"📌 **ID wiadomości:** `{msg.id}`\n\n"
            f"Teraz możesz dodać do niej role używając komendy:\n"
            f"`/reactionrole add message_id:{msg.id} emoji:<emotka> role:<@rola>`"
        )
        await ctx.send(info_msg, ephemeral=True if ctx.interaction else False)

    # ==========================================
    # LISTENERY REAKCJI
    # ==========================================

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id or payload.user_id == self.bot.user.id:
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT emoji, role_id
            FROM reaction_roles
            WHERE guild_id = ? AND message_id = ?
            """,
            (payload.guild_id, payload.message_id)
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = payload.member
        if not member:
            try:
                member = await guild.fetch_member(payload.user_id)
            except Exception:
                return

        if member.bot:
            return

        for saved_emoji, role_id in rows:
            if is_emoji_match(saved_emoji, payload.emoji):
                role = guild.get_role(role_id)
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role, reason="Role za reakcje (Reaction Role)")
                        logger.info(f"Przyznano rolę {role.name} użytkownikowi {member.name} ({member.id}) w {guild.name}")
                    except discord.Forbidden:
                        logger.warning(f"Brak uprawnień do dodania roli {role.name} w {guild.name}")
                    except Exception as e:
                        logger.error(f"Błąd dodawania roli za reakcję: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id or payload.user_id == self.bot.user.id:
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT emoji, role_id
            FROM reaction_roles
            WHERE guild_id = ? AND message_id = ?
            """,
            (payload.guild_id, payload.message_id)
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        try:
            member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        except Exception:
            return

        if not member or member.bot:
            return

        for saved_emoji, role_id in rows:
            if is_emoji_match(saved_emoji, payload.emoji):
                role = guild.get_role(role_id)
                if role and role in member.roles:
                    try:
                        await member.remove_roles(role, reason="Role za reakcje - usunięcie reakcji")
                        logger.info(f"Odebrano rolę {role.name} użytkownikowi {member.name} ({member.id}) w {guild.name}")
                    except discord.Forbidden:
                        logger.warning(f"Brak uprawnień do usunięcia roli {role.name} w {guild.name}")
                    except Exception as e:
                        logger.error(f"Błąd usuwania roli za reakcję: {e}")


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))