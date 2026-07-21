from discord.ext import commands
from core.config import OWNER_ID
from core.logger import log_info


class Owner(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    def is_owner(self, ctx):
        return ctx.author.id == OWNER_ID


    @commands.command()
    async def status(self, ctx):

        if not self.is_owner(ctx):
            await ctx.send("❌ Brak dostępu.")
            return

        members = sum(
            g.member_count or 0
            for g in self.bot.guilds
        )

        await ctx.send(
            f"""
🤖 Iris Status

Nazwa: {self.bot.user}
ID: {self.bot.user.id}
Serwery: {len(self.bot.guilds)}
Użytkownicy: {members}
"""
        )

        log_info(
            f"{ctx.author} sprawdził status Iris"
        )


    @commands.command()
    async def reload(self, ctx, extension=None):

        if not self.is_owner(ctx):
            await ctx.send("❌ Brak dostępu.")
            return


        extensions = [
            "commands.basic",
            "commands.iris_ai",
            "commands.welcome",
            "commands.moderation",
            "commands.errors",
            "commands.owner",
            "commands.status"
        ]


        if extension:

            try:
                await self.bot.reload_extension(
                    f"commands.{extension}"
                )

                await ctx.send(
                    f"♻️ Przeładowano moduł: `{extension}`"
                )

            except Exception as e:

                await ctx.send(
                    f"❌ Błąd reload:\n```{e}```"
                )

            return


        for ext in extensions:

            try:
                await self.bot.reload_extension(ext)

            except Exception as e:

                await ctx.send(
                    f"❌ Błąd przy {ext}:\n```{e}```"
                )

                return


        await ctx.send(
            "♻️ Przeładowano wszystkie moduły Iris."
        )

        log_info(
            f"{ctx.author} przeładował wszystkie moduły"
        )


async def setup(bot):
    await bot.add_cog(Owner(bot))