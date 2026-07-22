from discord.ext import commands

from core.logger import get_logger


class BaseCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(self.__class__.__name__)

    @property
    def db(self):
        return self.bot.database

    @property
    def cache(self):
        return self.bot.cache

    @property
    def guilds(self):
        return self.bot.guilds_repo

    @property
    def warnings(self):
        return self.bot.warnings_repo