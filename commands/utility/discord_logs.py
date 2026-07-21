from discord.ext import commands
from core.database import get_connection


class DiscordLogs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    async def send_log(self, guild, message):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT log_channel
            FROM guilds
            WHERE guild_id = ?
            """,
            (guild.id,)
        )

        data = cursor.fetchone()

        conn.close()


        if not data or not data[0]:
            return


        channel = guild.get_channel(data[0])

        if channel:
            await channel.send(message)



    @commands.Cog.listener()
    async def on_member_join(self, member):

        await self.send_log(
            member.guild,
            f"🟢 Dołączył użytkownik: {member.mention}\nID: `{member.id}`"
        )


    @commands.Cog.listener()
    async def on_member_remove(self, member):

        await self.send_log(
            member.guild,
            f"🔴 Użytkownik wyszedł: {member}\nID: `{member.id}`"
        )


    @commands.Cog.listener()
    async def on_message_delete(self, message):

        if message.guild is None:
            return

        if message.author.bot:
            return


        await self.send_log(
            message.guild,
            f"🗑️ Usunięto wiadomość\n"
            f"Autor: {message.author}\n"
            f"Kanał: {message.channel}\n"
            f"Treść: {message.content}"
        )


    @commands.Cog.listener()
    async def on_command(self, ctx):

        if ctx.guild is None:
            return

        await self.send_log(
            ctx.guild,
            f"⚙️ Komenda:\n"
            f"Użytkownik: {ctx.author}\n"
            f"`{ctx.message.content}`"
        )



async def setup(bot):
    await bot.add_cog(DiscordLogs(bot))