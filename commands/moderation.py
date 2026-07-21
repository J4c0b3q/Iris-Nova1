from discord.ext import commands
from core.logger import log_info


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):

        await ctx.channel.purge(limit=amount + 1)

        await ctx.send(
            f"🧹 Usunięto {amount} wiadomości.",
            delete_after=5
        )

        log_info(
            f"{ctx.author} usunął {amount} wiadomości na {ctx.channel}"
        )


    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: commands.MemberConverter, *, reason="Brak powodu"):

        await member.kick(reason=reason)

        await ctx.send(
            f"👢 {member} został wyrzucony. Powód: {reason}"
        )

        log_info(
            f"{ctx.author} wyrzucił {member}: {reason}"
        )


    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: commands.MemberConverter, *, reason="Brak powodu"):

        await member.ban(reason=reason)

        await ctx.send(
            f"🔨 {member} został zbanowany. Powód: {reason}"
        )

        log_info(
            f"{ctx.author} zbanował {member}: {reason}"
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))