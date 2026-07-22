import asyncio
import signal
import sys
from core.bot import IrisBot
from core.config import BOT_NAME, VERSION
from core.env import Env
from core.logger import get_logger

from database.database import init_database
from database.repositories.guild_repository import GuildRepository
from database.repositories.warning_repository import WarningRepository

logger = get_logger("Iris")


async def shutdown(bot: IrisBot):
    """Bezpiecznie zamyka połączenia bota i bazy danych."""
    logger.info("Rozpoczynanie bezpiecznego zamykania bota Iris...")
    if hasattr(bot, "database") and bot.database:
        try:
            bot.database.close()
            logger.info("Baza danych została pomyślnie zamknięta.")
        except Exception as e:
            logger.error(f"Błąd podczas zamykania bazy danych: {e}")
            
    if not bot.is_closed():
        await bot.close()
        logger.info("Połączenie z Discordem zostało pomyślnie zamknięte.")


async def main():
    logger.info("Startowanie Iris Nova...")

    # 1. Sprawdzenie tokenu Discorda
    if not Env.DISCORD_TOKEN:
        logger.critical("Brak DISCORD_TOKEN w pliku .env lub zmiennych środowiskowych!")
        sys.exit(1)

    # 2. Tworzenie instancji bota
    bot = IrisBot()

    # 3. Obsługa sygnałów systemowych do łagodnego wyłączania
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(bot)))
            except NotImplementedError:
                pass  # Windows nie obsługuje niektórych sygnałów w pętli asyncio
    except Exception as e:
        logger.warning(f"Nie udało się zarejestrować handlerów sygnałów: {e}")

    # 4. Inicjalizacja bazy danych i repozytoriów
    try:
        bot.database = init_database()
        bot.guilds_repo = GuildRepository(bot.database)
        bot.warnings_repo = WarningRepository(bot.database)
        logger.info("Baza danych oraz repozytoria zainicjalizowane.")
    except Exception as e:
        logger.critical(f"Krytyczny błąd podczas inicjalizacji bazy danych: {e}")
        return

    # 5. Uruchomienie bota
    try:
        async with bot:
            logger.info("Łączenie z serwerami Discord...")
            await bot.start(Env.DISCORD_TOKEN)
    except asyncio.CancelledError:
        logger.info("Zadanie główne zostało anulowane.")
    except Exception as e:
        logger.exception(f"Fatalny błąd podczas działania bota: {e}")
    finally:
        await shutdown(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Bot został wyłączony przez użytkownika.")
    except Exception:
        logger.exception("Krytyczna awaria procesu Iris.")