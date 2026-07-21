from discord.ext import commands

from core.config import BOT_NAME, VERSION
from core.logger import log_info


class Ready(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):

        try:

            print(
                "🔎 Aktualne slash commands:"
            )

            for command in self.bot.tree.get_commands():
                print(
                    f" - /{command.name}"
                )


            synced = await self.bot.tree.sync()


            print(
                f"🌙 Zsynchronizowano {len(synced)} slash commands"
            )


        except Exception as e:

            print(
                f"❌ Błąd synchronizacji slash: {e}"
            )


        print(
            f"{BOT_NAME} v{VERSION} działa jako {self.bot.user}"
        )


        log_info(
            f"Bot uruchomiony jako {self.bot.user}"
        )


async def setup(bot):

    await bot.add_cog(
        Ready(bot)
    )