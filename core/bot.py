import discord
from discord.ext import commands

from core.cache import Cache
from core.config import PREFIX, VERSION
from core.logger import get_logger
from database.repositories.guild_repository import GuildRepository
from database.repositories.warning_repository import WarningRepository


class IrisBot(commands.Bot):

    def __init__(self):

        intents = discord.Intents.all()

        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None,
        )

        self.logger = get_logger("Iris")

        self.version = VERSION

        self.loaded_modules = 0
        self.failed_modules = 0

        self.database = None
        self.guilds = None
        self.warnings = None

        self.cache = Cache()

        self.start_time = None

    async def setup_hook(self):

        from core.loader import load_extensions

        await load_extensions(self)

        self.logger.info("=" * 60)
        self.logger.info(
            f"Loaded {self.loaded_modules} modules."
        )
        self.logger.info(
            f"Failed {self.failed_modules} modules."
        )
        self.logger.info("=" * 60)