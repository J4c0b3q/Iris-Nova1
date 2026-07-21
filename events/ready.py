from discord.ext import commands

from core.config import BOT_NAME, VERSION
from core.logger import log_info


class Ready(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):

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