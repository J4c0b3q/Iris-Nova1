from discord.ext import commands
from core.database import get_connection


class ModConfig(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def modconfig(self, ctx, option=None, value=None):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT OR IGNORE INTO moderation_settings
            (guild_id)
            VALUES (?)
            """,
            (ctx.guild.id,)
        )


        if option and value:

            if option == "timeout":
                cursor.execute(
                    """
                    UPDATE moderation_settings
                    SET timeout_warns = ?
                    WHERE guild_id = ?
                    """,
                    (int(value), ctx.guild.id)
                )

            elif option == "kick":
                cursor.execute(
                    """
                    UPDATE moderation_settings
                    SET kick_warns = ?
                    WHERE guild_id = ?
                    """,
                    (int(value), ctx.guild.id)
                )

            elif option == "ban":
                cursor.execute(
                    """
                    UPDATE moderation_settings
                    SET ban_warns = ?
                    WHERE guild_id = ?
                    """,
                    (int(value), ctx.guild.id)
                )


            conn.commit()
            conn.close()


            await ctx.send(
                f"⚙️ Ustawiono {option}: {value} ostrzeżeń"
            )
            return



        cursor.execute(
            """
            SELECT timeout_warns, kick_warns, ban_warns
            FROM moderation_settings
            WHERE guild_id = ?
            """,
            (ctx.guild.id,)
        )


        data = cursor.fetchone()

        conn.close()


        await ctx.send(
            f"""
🛡️ **Moderacja Iris**

🔇 Timeout:
`{data[0]}` ostrzeżeń

👢 Kick:
`{data[1]}` ostrzeżeń

🔨 Ban:
`{data[2]}` ostrzeżeń
"""
        )


async def setup(bot):
    await bot.add_cog(ModConfig(bot))