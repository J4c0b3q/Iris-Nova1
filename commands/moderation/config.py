from discord.ext import commands
from core.database import get_connection


class Config(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx, option):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT OR IGNORE INTO guilds (guild_id)
            VALUES (?)
            """,
            (ctx.guild.id,)
        )


        if option == "logs":

            cursor.execute(
                """
                UPDATE guilds
                SET log_channel = ?
                WHERE guild_id = ?
                """,
                (
                    ctx.channel.id,
                    ctx.guild.id
                )
            )

            await ctx.send(
                f"✅ Kanał logów ustawiony: {ctx.channel.mention}"
            )


        elif option == "welcome":

            cursor.execute(
                """
                UPDATE guilds
                SET welcome_channel = ?
                WHERE guild_id = ?
                """,
                (
                    ctx.channel.id,
                    ctx.guild.id
                )
            )

            await ctx.send(
                f"✅ Kanał powitań ustawiony: {ctx.channel.mention}"
            )


        conn.commit()
        conn.close()



    @commands.command()
    async def config(self, ctx):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT log_channel, welcome_channel, prefix
            FROM guilds
            WHERE guild_id = ?
            """,
            (ctx.guild.id,)
        )


        data = cursor.fetchone()

        conn.close()


        if not data:
            await ctx.send(
                "⚠️ Ten serwer nie ma jeszcze konfiguracji."
            )
            return


        await ctx.send(
            f"""
⚙️ **Konfiguracja Iris**

📝 Logi:
`{data[0]}`

👋 Powitania:
`{data[1]}`

🔧 Prefix:
`{data[2]}`
"""
        )


async def setup(bot):
    await bot.add_cog(Config(bot))