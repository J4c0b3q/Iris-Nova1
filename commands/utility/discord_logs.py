import discord
from discord.ext import commands

from core.database import get_connection



class DiscordLogs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



    async def send_log(
        self,
        guild,
        embed
    ):


        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT log_channel
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



    @commands.Cog.listener()
    async def on_member_join(
        self,
        member
    ):


        embed = discord.Embed(
            title="🟢 Nowy użytkownik",
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
            embed
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


        embed.add_field(
            name="ID",
            value=str(member.id),
            inline=False
        )


        await self.send_log(
            member.guild,
            embed
        )



    @commands.Cog.listener()
    async def on_message_delete(
        self,
        message
    ):


        if message.guild is None:
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
            value=message.content[:1024]
            if message.content
            else "Brak tekstu",
            inline=False
        )


        await self.send_log(
            message.guild,
            embed
        )



    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction,
        command
    ):


        if interaction.guild is None:
            return


        embed = discord.Embed(
            title="⚙️ Wykonano slash command",
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


        await self.send_log(
            interaction.guild,
            embed
        )



async def setup(bot):

    await bot.add_cog(
        DiscordLogs(bot)
    )