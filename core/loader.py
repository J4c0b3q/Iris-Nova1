import time
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)


async def load_extensions(bot):
    commands_dir = Path("commands")

    bot.loaded_modules = 0
    bot.failed_modules = 0

    start = time.perf_counter()

    for file in commands_dir.rglob("*.py"):

        if file.name.startswith("_"):
            continue

        if file.name == "__init__.py":
            continue

        module = ".".join(file.with_suffix("").parts)

        try:
            module_start = time.perf_counter()

            await bot.load_extension(module)

            elapsed = time.perf_counter() - module_start

            bot.loaded_modules += 1

            logger.info(f"✓ {module} ({elapsed:.2f}s)")

        except Exception:

            bot.failed_modules += 1

            logger.exception(f"✗ {module}")

    total = time.perf_counter() - start

    logger.info("=" * 60)
    logger.info(f"Loaded: {bot.loaded_modules}")
    logger.info(f"Failed: {bot.failed_modules}")
    logger.info(f"Time: {total:.2f}s")
    logger.info("=" * 60)