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

            "member":
            "member_log_channel",

            "moderation":
            "moderation_log_channel",

            "message":
            "message_log_channel"

        }


        column = columns.get(
            log_type
        )


        if not column:
            return



        cursor.execute(
            f"""
            SELECT {column}
            FROM guilds
            WHERE guild_id = ?
            """,
            (
                guild.id,
            )
        )


        data = cursor.fetchone()


        conn.close()



        if not data or not data[0]:
            return



        channel = guild.get_channel(
            data[0]
        )


        if channel:

            await channel.send(
                embed=embed
            )



    # =====================
    # MEMBER LOGS
    # =====================


    @commands.Cog.listener()
    async def on_member_join(
        self,
        member
    ):


        embed = discord.Embed(
            title="🟢 Użytkownik dołączył",
            color=discord.Color.green()
        )


        embed.add_field(
            name="Użytkownik",
            value=member.mention,
            inline=False
        )


        embed.add_field(
            name="ID",
            value=str(member.id),
            inline=False
        )


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
            value=str(member),
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


        if not message.guild:
            return


        if message.author.bot:
            return



        embed = discord.Embed(
            title="🗑️ Usunięto wiadomość",
            color=discord.Color.orange()
        )


        embed.add_field(
            name="Autor",
            value=str(message.author),
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
                else "Brak treści"
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
            title="🔨 Ban użytkownika",
            color=discord.Color.red()
        )


        embed.add_field(
            name="Użytkownik",
            value=str(user),
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
            title="🔓 Zdjęto bana",
            color=discord.Color.green()
        )


        embed.add_field(
            name="Użytkownik",
            value=str(user),
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
            title="⚙️ Wykonano komendę",
            color=discord.Color.blue()
        )


        embed.add_field(
            name="Użytkownik",
            value=str(interaction.user),
            inline=False
        )


        embed.add_field(
            name="Komenda",
            value=f"/{command.name}",
            inline=False
        )


        # komendy moderacyjne lecą do moderacji
        moderation_commands = [

            "ban",
            "kick",
            "warn",
            "clear",
            "clearwarns"

        ]


        log_type = (
            "moderation"
            if command.name in moderation_commands
            else "message"
        )


        await self.send_log(
            interaction.guild,
            embed,
            log_type
        )



async def setup(bot):

    await bot.add_cog(
        DiscordLogs(bot)
    )