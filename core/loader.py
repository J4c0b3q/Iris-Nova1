import time
from pathlib import Path
from core.logger import get_logger

logger = get_logger("Loader")


async def load_extensions(bot):
    # Przeszukuj oba katalogi: commands oraz events
    source_dirs = [Path("commands"), Path("events")]

    bot.loaded_modules = 0
    bot.failed_modules = 0

    start = time.perf_counter()

    for folder in source_dirs:
        if not folder.exists():
            continue

        for file in folder.rglob("*.py"):
            if file.name.startswith("_") or file.name == "__init__.py":
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
                logger.exception(f"✗ Błąd ładowania rozszerzenia {module}")

    total = time.perf_counter() - start

    logger.info("=" * 60)
    logger.info(f"Załadowano rozszerzeń: {bot.loaded_modules}")
    if bot.failed_modules > 0:
        logger.warning(f"Błędy ładowania: {bot.failed_modules}")
    logger.info(f"Czas ładowania: {total:.2f}s")
    logger.info("=" * 60)