import discord
from discord.ext import commands

from database.database import get_connection


class DiscordLogs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def send_log(
        self,
        guild,
        embed,
        log_type
    ):
        conn = get_connection()
        cursor = conn.cursor()

        columns = {
            "member": "member_log_channel",
            "moderation": "moderation_log_channel",
            "message": "message_log_channel"
        }

        column = columns.get(log_type)
        if not column:
            conn.close()
            return

        cursor.execute(
            f"""
            SELECT {column}, log_channel
            FROM guilds
            WHERE guild_id = ?
            """,
            (
                guild.id,
            )
        )

        data = cursor.fetchone()
        conn.close()

        if not data:
            return

        # Dedykowany kanał logowania lub fallback do głównego log_channel
        channel_id = data[0] or data[1]
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

    # =====================
    # MEMBER LOGS
    # =====================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member
    ):
        embed = discord.Embed(
            title="🟢 Użytkownik dołączył do serwera",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Użytkownik",
            value=f"{member.mention} (`{member}`)",
            inline=False
        )
        embed.add_field(
            name="ID Użytkownika",
            value=str(member.id),
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        await self.send_log(
            member.guild,
            embed,
            "member"
        )

    @commands.Cog.listener()
    async def on_member_remove(
        self,
        member
    ):
        embed = discord.Embed(
            title="🔴 Użytkownik opuścił serwer",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Użytkownik",
            value=f"{member.mention} (`{member}`)",
            inline=False
        )
        embed.add_field(
            name="ID Użytkownika",
            value=str(member.id),
            inline=False
        )

        await self.send_log(
            member.guild,
            embed,
            "member"
        )

    # =====================
    # MESSAGE LOGS
    # =====================

    @commands.Cog.listener()
    async def on_message_delete(
        self,
        message
    ):
        if not message.guild or message.author.bot:
            return

        embed = discord.Embed(
            title="🗑️ Usunięto wiadomość",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Autor",
            value=f"{message.author.mention} (`{message.author}`)",
            inline=False
        )
        embed.add_field(
            name="Kanał",
            value=message.channel.mention,
            inline=False
        )
        embed.add_field(
            name="Treść",
            value=(
                message.content[:1024]
                if message.content
                else "*Brak treści tekstowej (załącznik lub komenda)*"
            ),
            inline=False
        )

        await self.send_log(
            message.guild,
            embed,
            "message"
        )

    # =====================
    # MODERATION LOGS
    # =====================

    @commands.Cog.listener()
    async def on_member_ban(
        self,
        guild,
        user
    ):
        embed = discord.Embed(
            title="🔨 Zbanowano użytkownika",
            color=discord.Color.dark_red()
        )
        embed.add_field(
            name="Użytkownik",
            value=f"{user.mention} (`{user}`)",
            inline=False
        )
        embed.add_field(
            name="ID",
            value=str(user.id),
            inline=False
        )

        await self.send_log(
            guild,
            embed,
            "moderation"
        )

    @commands.Cog.listener()
    async def on_member_unban(
        self,
        guild,
        user
    ):
        embed = discord.Embed(
            title="🔓 Odblokowano użytkownika (Unban)",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Użytkownik",
            value=f"{user.mention} (`{user}`)",
            inline=False
        )

        await self.send_log(
            guild,
            embed,
            "moderation"
        )

    # =====================
    # SLASH COMMAND LOGS
    # =====================

    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction,
        command
    ):
        if not interaction.guild:
            return

        embed = discord.Embed(
            title="⚙️ Użyto komendy slash",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Użytkownik",
            value=f"{interaction.user.mention} (`{interaction.user}`)",
            inline=False
        )
        embed.add_field(
            name="Komenda",
            value=f"`/{command.name}`",
            inline=False
        )

        await self.send_log(
            interaction.guild,
            embed,
            "moderation"
        )


async def setup(bot):
    await bot.add_cog(
        DiscordLogs(bot)
    )