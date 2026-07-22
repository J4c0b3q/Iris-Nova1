import os
from dotenv import load_dotenv

load_dotenv()


class Env:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    @classmethod
    def validate(cls) -> bool:
        """Sprawdza czy kluczowe zmienne są prawidłowo zdefiniowane."""
        missing = []
        if not cls.DISCORD_TOKEN:
            missing.append("DISCORD_TOKEN")
        
        if missing:
            print(f"[ENV ERROR] Brakujące zmienne w .env: {', '.join(missing)}")
            return False
        return True


if not Env.DISCORD_TOKEN:
    print("[WARNING] DISCORD_TOKEN nie został odnaleziony w środowisku!")