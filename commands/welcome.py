from discord.ext import commands
from core.database import get_connection


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    async def get_welcome_channel(self, guild):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT welcome_channel
            FROM guilds
            WHERE guild_id = ?
            """,
            (guild.id,)
        )

        data = cursor.fetchone()

        conn.close()

        if not data or not data[0]:
            return None

        return guild.get_channel(data[0])


    @commands.Cog.listener()
    async def on_member_join(self, member):

        channel = await self.get_welcome_channel(
            member.guild
        )

        if channel:

            await channel.send(
                f"🌙 Witaj {member.mention} na serwerze!\n"
            )


async def setup(bot):
    await bot.add_cog(Welcome(bot))