import discord
from discord.ext import commands
from discord import app_commands

from core.logger import get_logger
from database.database import get_connection

logger = get_logger("Boost")


class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    boost_group = app_commands.Group(
        name="boost",
        description="Komendy do zarządzania powiadomieniami o ulepszeniach (boostach) serwera"
    )

    async def get_boost_channel_and_msg(self, guild: discord.Guild):
        """Pobiera skonfigurowany kanał i treść wiadomości dla danego serwera."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT channel_id, custom_message FROM boost_settings WHERE guild_id = ?",
            (guild.id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            return None, None

        channel = guild.get_channel(row[0])
        return channel, row[1]

    async def send_boost_embed(self, guild: discord.Guild, member: discord.Member, custom_msg: str = None):
        """Pomocnicza funkcja generująca i wysyłająca efektowny Embed o booscie."""
        channel, saved_msg = await self.get_boost_channel_and_msg(guild)
        if not channel:
            channel = guild.system_channel

        if not channel:
            return

        description_text = custom_msg or saved_msg or (
            f"🚀 **Dziękujemy za ulepszenie serwera!**\n\n"
            f"{member.mention} właśnie ulepszył(a) **{guild.name}**! 🎉\n"
            f"Dzięki Tobie serwer rozwija się jeszcze szybciej! ❤️"
        )

        embed = discord.Embed(
            title="💎 NOWY BOOST SERWERA!",
            description=description_text,
            color=discord.Color.from_rgb(244, 127, 255)  # Różowy kolor Discord Boost
        )

        if member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="🚀 Liczba Ulepszeń",
            value=f"**{guild.premium_subscription_count or 0}** boostów",
            inline=True
        )

        embed.add_field(
            name="⭐ Poziom Serwera",
            value=f"Poziom **{guild.premium_tier}**",
            inline=True
        )

        embed.set_footer(
            text=f"🌙 Iris Nova • Boost {member.display_name}",
            icon_url=guild.icon.url if guild.icon else None
        )

        try:
            await channel.send(content=f"🚀 {member.mention}", embed=embed)
            logger.info(f"Wysłano powiadomienie o booscie od {member} na kanale {channel.name} ({guild.name})")
        except Exception as e:
            logger.error(f"Nie udało się wysłać powiadomienia o booscie: {e}")

    # ==========================
    # LISTENERY ZDARZEŃ
    # ==========================

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Wykrywa moment dodania boosta przez członka serwera."""
        if before.premium_since is None and after.premium_since is not None:
            await self.send_boost_embed(after.guild, after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Wykrywa wiadomości systemowe o ulepszeniu serwera."""
        if not message.guild or message.author.bot:
            return

        boost_types = (
            discord.MessageType.premium_guild_subscription,
            discord.MessageType.premium_guild_tier_1,
            discord.MessageType.premium_guild_tier_2,
            discord.MessageType.premium_guild_tier_3,
        )

        if message.type in boost_types:
            member = message.author
            if isinstance(member, discord.Member):
                channel, _ = await self.get_boost_channel_and_msg(message.guild)
                if channel and channel.id != message.channel.id:
                    await self.send_boost_embed(message.guild, member)

    # ==========================
    # KOMENDY SLASH
    # ==========================

    @boost_group.command(
        name="setup",
        description="Konfiguruje kanał do wysyłania powiadomień o ulepszeniach serwera (boost)"
    )
    @app_commands.describe(
        channel="Kanał tekstowy, na który będą wysyłane powiadomienia o boostach",
        message="Opcjonalna własna treść powiadomienia (użyj {member} dla wzmianki, {guild} dla nazwy serwera)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str = None
    ):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        guild = interaction.guild

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO boost_settings (guild_id, channel_id, custom_message)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                custom_message = excluded.custom_message
            """,
            (guild.id, channel.id, message)
        )
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="🚀 Powiadomienia o Boostach Skonfigurowane",
            description=(
                f"✅ Pomyślnie ustawiono kanał powiadomień o ulepszeniach: {channel.mention}\n\n"
                f"**Niestandardowa wiadomość:** {message if message else 'Domyślna'}"
            ),
            color=discord.Color.from_rgb(244, 127, 255)
        )
        embed.set_footer(text="🌙 Iris Nova • Powiadomienia Boost")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @boost_group.command(
        name="test",
        description="Wysyła testowe powiadomienie o booscie na skonfigurowany kanał"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def test(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        channel, _ = await self.get_boost_channel_and_msg(interaction.guild)
        target = channel or interaction.channel

        await self.send_boost_embed(interaction.guild, interaction.user)
        await interaction.followup.send(
            f"✅ Wysłąno testowe powiadomienie o booscie na kanał {target.mention}!",
            ephemeral=True
        )

    @boost_group.command(
        name="status",
        description="Wyświetla aktualny stan ulepszeń (boostów) serwera"
    )
    async def status(self, interaction: discord.Interaction):
        guild = interaction.guild
        boosters = [m for m in guild.members if m.premium_since is not None]

        embed = discord.Embed(
            title=f"💎 Statystyki Boostów • {guild.name}",
            color=discord.Color.from_rgb(244, 127, 255)
        )

        embed.add_field(name="🚀 Liczba Boostów", value=f"**{guild.premium_subscription_count or 0}**", inline=True)
        embed.add_field(name="⭐ Poziom Serwera", value=f"Poziom **{guild.premium_tier}**", inline=True)
        embed.add_field(name="👑 Osoby Boostujące", value=f"**{len(boosters)}** osób", inline=True)

        if boosters:
            booster_list = ", ".join([b.mention for b in boosters[:10]])
            if len(boosters) > 10:
                booster_list += f" oraz **{len(boosters) - 10}** innych..."
            embed.add_field(name="💖 Nasi Boosterzy", value=booster_list, inline=False)

        embed.set_footer(text="🌙 Iris Nova • Server Boost")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @boost_group.command(
        name="remove",
        description="Wyłącza dedykowane powiadomienia o boostach"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def remove(self, interaction: discord.Interaction):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM boost_settings WHERE guild_id = ?", (interaction.guild.id,))
        conn.commit()
        conn.close()

        await interaction.response.send_message(
            "🗑️ Dedykowane powiadomienia o boostach zostały wyłączone.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Boost(bot))