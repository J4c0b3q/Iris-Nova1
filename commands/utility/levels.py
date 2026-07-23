import random
import time
import discord
from discord.ext import commands

from database.database import get_connection
from core.logger import get_logger

logger = get_logger("Levels")


def get_xp_for_level(level: int) -> int:
    """Oblicza sumaryczny XP wymagany do osiągnięcia danego poziomu."""
    if level <= 0:
        return 0
    return int(100 * (level ** 1.5)) + (level * 50)


def get_level_from_xp(xp: int) -> int:
    """Wyznacza poziom na podstawie zgromadzonego XP."""
    level = 0
    while get_xp_for_level(level + 1) <= xp:
        level += 1
    return level


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Słownik z czasem ostatnio przyznanego XP: (guild_id, user_id) -> timestamp
        self._cooldowns = {}

    def get_user_data(self, guild_id: int, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT xp, level, messages
            FROM user_levels
            WHERE guild_id = ? AND user_id = ?
            """,
            (guild_id, user_id),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"xp": row[0], "level": row[1], "messages": row[2]}
        return {"xp": 0, "level": 0, "messages": 0}

    def save_user_data(self, guild_id: int, user_id: int, xp: int, level: int, messages: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_levels (guild_id, user_id, xp, level, messages, last_xp_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                xp = excluded.xp,
                level = excluded.level,
                messages = excluded.messages,
                last_xp_at = CURRENT_TIMESTAMP
            """,
            (guild_id, user_id, xp, level, messages),
        )
        conn.commit()
        conn.close()

    def get_level_channel_id(self, guild_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT level_channel
            FROM guilds
            WHERE guild_id = ?
            """,
            (guild_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] else None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignoruj boty, wiadomości prywatne oraz komendy
        if message.author.bot or not message.guild or message.content.startswith(("/", "!")):
            return

        guild_id = message.guild.id
        user_id = message.author.id
        now = time.time()

        # Cooldown 60 sekund na przyznawanie XP
        key = (guild_id, user_id)
        if key in self._cooldowns and now - self._cooldowns[key] < 60:
            return

        self._cooldowns[key] = now

        user_data = self.get_user_data(guild_id, user_id)
        current_xp = user_data["xp"]
        current_level = user_data["level"]
        message_count = user_data["messages"] + 1

        # Losuj 15-25 XP za wiadomość
        gained_xp = random.randint(15, 25)
        new_xp = current_xp + gained_xp
        new_level = get_level_from_xp(new_xp)

        self.save_user_data(guild_id, user_id, new_xp, new_level, message_count)

        # Awans na nowy poziom!
        if new_level > current_level:
            channel_id = self.get_level_channel_id(guild_id)
            target_channel = None

            if channel_id:
                target_channel = message.guild.get_channel(channel_id)

            # Jeśli kanał nie jest ustawiony, powiadom na kanale wiadomości
            if not target_channel:
                target_channel = message.channel

            try:
                xp_for_next = get_xp_for_level(new_level + 1)
                embed = discord.Embed(
                    title="🎉 Awans na nowy poziom!",
                    description=(
                        f"Gratulacje {message.author.mention}! "
                        f"Twój poziom wzrósł na **{new_level}**! 🚀\n"
                        f"Zdobyto łącznie **{new_xp} XP**."
                    ),
                    color=discord.Color.gold(),
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                embed.add_field(name="🎖 Nowy poziom", value=f"**Level {new_level}**", inline=True)
                embed.add_field(name="✨ Następny poziom", value=f"**{xp_for_next} XP**", inline=True)
                embed.set_footer(text="🌙 Iris Nova • Pisz wiadomości, aby zdobywać XP!")

                await target_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Nie udało się wysłać powiadomienia o level-up: {e}")

    @commands.hybrid_command(
        name="rank",
        description="Wyświetla Twój aktualny poziom, XP oraz statystyki na serwerze"
    )
    @discord.app_commands.describe(
        user="Użytkownik, którego poziom chcesz sprawdzić (opcjonalnie)"
    )
    async def rank(self, ctx: commands.Context, user: discord.Member = None):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        target = user or ctx.author
        guild_id = ctx.guild.id

        data = self.get_user_data(guild_id, target.id)
        current_xp = data["xp"]
        current_level = data["level"]
        messages = data["messages"]

        # Oblicz pozycję w rankingu
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) + 1
            FROM user_levels
            WHERE guild_id = ? AND (xp > ? OR (xp = ? AND user_id < ?))
            """,
            (guild_id, current_xp, current_xp, target.id),
        )
        rank_pos = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM user_levels WHERE guild_id = ?",
            (guild_id,),
        )
        total_users = cursor.fetchone()[0] or 1
        conn.close()

        # Postęp do następnego poziomu
        xp_start = get_xp_for_level(current_level)
        xp_end = get_xp_for_level(current_level + 1)
        needed_for_level = xp_end - xp_start
        current_progress_xp = max(0, current_xp - xp_start)

        progress_pct = min(1.0, current_progress_xp / needed_for_level) if needed_for_level > 0 else 1.0
        filled_blocks = int(progress_pct * 10)
        progress_bar = "█" * filled_blocks + "░" * (10 - filled_blocks)

        embed = discord.Embed(
            title=f"📊 Karta Poziomu — {target.display_name}",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 Poziom", value=f"**Level {current_level}**", inline=True)
        embed.add_field(name="🥇 Pozycja w rankingu", value=f"**#{rank_pos}** / {total_users}", inline=True)
        embed.add_field(name="💬 Wysłane wiadomości", value=f"**{messages}**", inline=True)

        embed.add_field(
            name="✨ Postęp XP do poziomu " + str(current_level + 1),
            value=f"`[{progress_bar}]` {int(progress_pct * 100)}%\n**{current_xp}** / **{xp_end} XP** (potrzeba jeszcze **{xp_end - current_xp} XP**)",
            inline=False,
        )

        embed.set_footer(text="🌙 Iris Nova • Pisz wiadomości na serwerze, aby zdobywać kolejne poziomy!")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="leaderboard",
        aliases=["top"],
        description="Wyświetla ranking najaktywniejszych użytkowników na serwerze"
    )
    async def leaderboard(self, ctx: commands.Context):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        guild_id = ctx.guild.id

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, level, xp, messages
            FROM user_levels
            WHERE guild_id = ?
            ORDER BY xp DESC, level DESC
            LIMIT 10
            """,
            (guild_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await ctx.send(
                "📉 Brak danych w rankingu. Zacznijcie pisać wiadomości, aby zdobywać XP!",
                ephemeral=True,
            )
            return

        description = ""
        medals = ["🥇", "🥈", "🥉"]

        for idx, (u_id, lvl, xp, msgs) in enumerate(rows, start=1):
            member = ctx.guild.get_member(u_id)
            name = member.mention if member else f"<@{u_id}>"
            icon = medals[idx - 1] if idx <= 3 else f"**{idx}.**"

            description += f"{icon} {name} — **Lvl {lvl}** ({xp} XP, {msgs} wiadomości)\n"

        embed = discord.Embed(
            title=f"🏆 Ranking Aktywności — {ctx.guild.name}",
            description=description,
            color=discord.Color.gold(),
        )
        embed.set_footer(text="🌙 Iris Nova • Zdobądź więcej XP pisząc na czacie!")

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="set_level_channel",
        description="Ustawia dedykowany kanał dla powiadomień o awansach (level-up)"
    )
    @discord.app_commands.describe(
        channel="Wybierz kanał tekstowy lub pozostaw puste, aby wyczyścić ustawienie"
    )
    @commands.has_permissions(administrator=True)
    async def set_level_channel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR IGNORE INTO guilds (guild_id) VALUES (?)",
            (ctx.guild.id,),
        )

        ch_id = channel.id if channel else None
        cursor.execute(
            "UPDATE guilds SET level_channel = ? WHERE guild_id = ?",
            (ch_id, ctx.guild.id),
        )
        conn.commit()
        conn.close()

        if channel:
            msg = f"✅ Dedykowany kanał awansów został ustawiony na {channel.mention}!"
        else:
            msg = "ℹ️ Usunięto dedykowany kanał awansów. Powiadomienia będą wysyłane na bieżącym kanale."

        await ctx.send(msg, ephemeral=True)

    @commands.hybrid_command(
        name="add_xp",
        aliases=["addxp"],
        description="[Admin] Dodaje Punkty Doświadczenia (XP) wybranemu użytkownikowi"
    )
    @discord.app_commands.describe(
        user="Użytkownik, któremu chcesz dodać XP",
        amount="Ilość XP do dodania"
    )
    @commands.has_permissions(administrator=True)
    async def add_xp(self, ctx: commands.Context, user: discord.Member, amount: int):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        if amount <= 0:
            await ctx.send("❌ Ilość XP musi być większa od 0.", ephemeral=True)
            return

        guild_id = ctx.guild.id
        data = self.get_user_data(guild_id, user.id)
        new_xp = data["xp"] + amount
        new_level = get_level_from_xp(new_xp)

        self.save_user_data(guild_id, user.id, new_xp, new_level, data["messages"])

        await ctx.send(
            f"✅ Dodano **{amount} XP** dla {user.mention}. Nowy poziom: **{new_level}** ({new_xp} XP).",
            ephemeral=True
        )

    @commands.hybrid_command(
        name="remove_xp",
        aliases=["removexp", "remove-xp"],
        description="[Admin] Usuwa Punkty Doświadczenia (XP) wybranemu użytkownikowi"
    )
    @discord.app_commands.describe(
        user="Użytkownik, któremu chcesz usunąć XP",
        amount="Ilość XP do usunięcia"
    )
    @commands.has_permissions(administrator=True)
    async def remove_xp(self, ctx: commands.Context, user: discord.Member, amount: int):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        if amount <= 0:
            await ctx.send("❌ Ilość XP musi być większa od 0.", ephemeral=True)
            return

        guild_id = ctx.guild.id
        data = self.get_user_data(guild_id, user.id)
        current_xp = data["xp"]
        new_xp = max(0, current_xp - amount)
        new_level = get_level_from_xp(new_xp)

        self.save_user_data(guild_id, user.id, new_xp, new_level, data["messages"])

        await ctx.send(
            f"✅ Usunięto **{amount} XP** użytkownikowi {user.mention}. Nowy poziom: **{new_level}** ({new_xp} XP).",
            ephemeral=True
        )

    @commands.hybrid_command(
        name="reset_lvl",
        aliases=["resetlvl", "resetlevel", "reset_level"],
        description="[Admin] Resetuje poziom oraz XP wybranego użytkownika do 0"
    )
    @discord.app_commands.describe(
        user="Użytkownik, którego poziom chcesz zresetować"
    )
    @commands.has_permissions(administrator=True)
    async def reset_lvl(self, ctx: commands.Context, user: discord.Member):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        guild_id = ctx.guild.id
        self.save_user_data(guild_id, user.id, 0, 0, 0)

        await ctx.send(
            f"✅ Zresetowano poziom, XP oraz statystyki użytkownika {user.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Levels(bot))