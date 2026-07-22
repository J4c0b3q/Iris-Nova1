import discord
from discord.ext import commands
from database.database import get_connection


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def get_welcome_channel(self, guild):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT welcome_channel FROM guilds WHERE guild_id = ?",
            (guild.id,)
        )
        data = cursor.fetchone()
        conn.close()

        if not data or not data[0]:
            return None

        return guild.get_channel(data[0])

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await self.get_welcome_channel(member.guild)
        if not channel:
            return

        embed = discord.Embed(
            title="🌙 Witamy na serwerze!",
            description=(
                f"Witaj {member.mention}!\n\n"
                f"Cieszymy się, że dołączyłeś/aś do **{member.guild.name}**."
            ),
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="👥 Użytkownik",
            value=str(member),
            inline=True
        )

        embed.add_field(
            name="📅 Konto utworzone",
            value=discord.utils.format_dt(member.created_at, style="R"),
            inline=False
        )

        embed.set_footer(text="🌙 Iris Nova")

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))