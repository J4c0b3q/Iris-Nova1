from discord.ext import commands
from core.database import get_connection
import datetime


class Warnings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: commands.MemberConverter, *, reason="Brak powodu"):

        conn = get_connection()
        cursor = conn.cursor()


        # zapis ostrzeżenia
        cursor.execute(
            """
            INSERT INTO warnings
            (guild_id, user_id, moderator_id, reason)
            VALUES (?, ?, ?, ?)
            """,
            (
                ctx.guild.id,
                member.id,
                ctx.author.id,
                reason
            )
        )


        # liczba ostrzeżeń
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                ctx.guild.id,
                member.id
            )
        )

        warns = cursor.fetchone()[0]


        # pobieranie ustawień moderacji
        cursor.execute(
            """
            SELECT timeout_warns, kick_warns, ban_warns
            FROM moderation_settings
            WHERE guild_id = ?
            """,
            (ctx.guild.id,)
        )

        settings = cursor.fetchone()


        if not settings:
             cursor.execute(
                 """
                 INSERT INTO moderation_settings
                 (guild_id)
                 VALUES (?)
                 """,
                  (ctx.guild.id,)
              )

             settings = (3, 5, 10)
        

        conn.commit()
        conn.close()


        await ctx.send(
            f"⚠️ {member.mention} otrzymał ostrzeżenie.\n"
            f"Powód: {reason}\n"
            f"Łącznie ostrzeżeń: {warns}"
        )


        if not settings:
            return


        timeout_warns = settings[0]
        kick_warns = settings[1]
        ban_warns = settings[2]

        
        print(
    f"DEBUG Iris: warny={warns}, timeout={timeout_warns}, kick={kick_warns}, ban={ban_warns}"
)

        # BAN
        if warns >= ban_warns:

            try:
                await member.ban(
                    reason="Iris: automatyczna kara za ostrzeżenia"
                )

                await ctx.send(
                    f"🔨 {member.mention} został zbanowany "
                    f"(osiągnięto {warns} ostrzeżeń)."
                )

            except:
                pass


        # KICK
        elif warns >= kick_warns:

            try:
                await member.kick(
                    reason="Iris: automatyczna kara za ostrzeżenia"
                )

                await ctx.send(
                    f"👢 {member.mention} został wyrzucony "
                    f"(osiągnięto {warns} ostrzeżeń)."
                )

            except:
                pass


        # TIMEOUT
        elif warns >= timeout_warns:

            try:
                until = datetime.datetime.now(
                    datetime.timezone.utc
                ) + datetime.timedelta(minutes=10)


                await member.timeout(
                    until,
                    reason="Iris: automatyczna kara za ostrzeżenia"
                )


                await ctx.send(
                    f"🔇 {member.mention} otrzymał timeout "
                    f"(osiągnięto {warns} ostrzeżeń)."
                )

            except:
                pass



    @commands.command()
    async def warnings(self, ctx, member: commands.MemberConverter):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT reason, date
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                ctx.guild.id,
                member.id
            )
        )


        data = cursor.fetchall()

        conn.close()


        if not data:
            await ctx.send(
                "✅ Ten użytkownik nie ma ostrzeżeń."
            )
            return


        text = ""

        for i, warning in enumerate(data, 1):
            text += (
                f"{i}. {warning[0]} "
                f"({warning[1]})\n"
            )


        await ctx.send(
            f"⚠️ Ostrzeżenia dla {member.mention}:\n\n{text}"
        )


async def setup(bot):
    await bot.add_cog(Warnings(bot))