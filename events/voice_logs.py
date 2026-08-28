import discord
from discord.ext import commands
import datetime
from database.database import get_connection
from core.logger import get_logger

logger = get_logger("VoiceLogs")


class VoiceLogs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT voice_log_channel, log_channel
                FROM guilds
                WHERE guild_id = ?
                """,
                (guild.id,),
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            voice_log_ch_id = row[0] or row[1]
            if voice_log_ch_id:
                return guild.get_channel(voice_log_ch_id)
        except Exception as e:
            logger.error(f"Błąd podczas pobierania kanału logów głosowych: {e}")
        return None

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        guild = member.guild
        log_channel = await self.get_log_channel(guild)
        if not log_channel:
            return

        embed = None
        now = datetime.datetime.now()
        timestamp_str = f"<t:{int(now.timestamp())}:f>"

        # 1. Dołączenie do kanału głosowego
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🔊 Połączono z kanałem głosowym",
                description=f"{member.mention} ({member.name}) dołączył do kanału głosowego {after.channel.mention}.",
                color=discord.Color.green(),
                timestamp=now
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Użytkownik", value=f"{member.mention} ({member.id})", inline=True)
            embed.add_field(name="Kanał", value=after.channel.name, inline=True)
            embed.add_field(name="Czas", value=timestamp_str, inline=False)

        # 2. Opuszczenie kanału głosowego
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="🔇 Rozłączono z kanałem głosowym",
                description=f"{member.mention} ({member.name}) opuścił kanał głosowy `{before.channel.name}`.",
                color=discord.Color.red(),
                timestamp=now
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Użytkownik", value=f"{member.mention} ({member.id})", inline=True)
            embed.add_field(name="Poprzedni Kanał", value=before.channel.name, inline=True)
            embed.add_field(name="Czas", value=timestamp_str, inline=False)

        # 3. Przejście do innego kanału głosowego
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            embed = discord.Embed(
                title="🔀 Przeniesiono kanał głosowy",
                description=f"{member.mention} ({member.name}) zmienił kanał głosowy.",
                color=discord.Color.blue(),
                timestamp=now
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Użytkownik", value=f"{member.mention} ({member.id})", inline=False)
            embed.add_field(name="Z kanału", value=before.channel.mention, inline=True)
            embed.add_field(name="Na kanał", value=after.channel.mention, inline=True)
            embed.add_field(name="Czas", value=timestamp_str, inline=False)

        # Wyślij log dołączenia/opuszczenia/przeniesienia, jeśli został utworzony
        if embed:
            try:
                await log_channel.send(embed=embed)
                # Ponieważ użytkownik zmienił stan kanału podstawowego, nie będziemy przetwarzać zmian streamu/kamery w tej samej wiadomości
                return
            except Exception as e:
                logger.error(f"Nie udało się wysłać logu głosowego (dołączenie/opuszczenie): {e}")

        # 4. Streamowanie (Udostępnianie ekranu)
        if before.self_stream != after.self_stream:
            if after.self_stream:
                embed = discord.Embed(
                    title="🖥️ Rozpoczęto udostępnianie ekranu",
                    description=f"{member.mention} ({member.name}) rozpoczął nadawanie strumienia (Stream) na kanale {after.channel.mention}.",
                    color=discord.Color.purple(),
                    timestamp=now
                )
            else:
                embed = discord.Embed(
                    title="🖥️ Zakończono udostępnianie ekranu",
                    description=f"{member.mention} ({member.name}) zakończył nadawanie strumienia (Stream) na kanale {after.channel.mention}.",
                    color=discord.Color.dark_magenta(),
                    timestamp=now
                )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Użytkownik", value=f"{member.mention} ({member.id})", inline=True)
            embed.add_field(name="Kanał", value=after.channel.mention if after.channel else "Brak", inline=True)
            embed.add_field(name="Czas", value=timestamp_str, inline=False)

            try:
                await log_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Nie udało się wysłać logu streamowania: {e}")

        # 5. Włączenie / wyłączenie kamery (Video)
        if before.self_video != after.self_video:
            if after.self_video:
                embed = discord.Embed(
                    title="📷 Włączono kamerę wideo",
                    description=f"{member.mention} ({member.name}) włączył kamerę wideo na kanale {after.channel.mention}.",
                    color=discord.Color.teal(),
                    timestamp=now
                )
            else:
                embed = discord.Embed(
                    title="📷 Wyłączono kamerę wideo",
                    description=f"{member.mention} ({member.name}) wyłączył kamerę wideo na kanale {after.channel.mention}.",
                    color=discord.Color.dark_teal(),
                    timestamp=now
                )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Użytkownik", value=f"{member.mention} ({member.id})", inline=True)
            embed.add_field(name="Kanał", value=after.channel.mention if after.channel else "Brak", inline=True)
            embed.add_field(name="Czas", value=timestamp_str, inline=False)

            try:
                await log_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Nie udało się wysłać logu wideo: {e}")


async def setup(bot):
    await bot.add_cog(VoiceLogs(bot))