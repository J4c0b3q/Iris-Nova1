import os
from dotenv import load_dotenv

load_dotenv()


class Env:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    OPENAI_KEY = os.getenv("OPENAI_KEY")


# Walidacja wymaganych zmiennych
if not Env.DISCORD_TOKEN:
    raise RuntimeError("Brak DISCORD_TOKEN w pliku .env")

if Env.OWNER_ID == 0:
    raise RuntimeError("Brak OWNER_ID w pliku .env")