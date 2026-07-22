import os
from core.env import Env
from core.personality import IRIS_PERSONALITY

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

_client = None


def get_openai_client():
    """Zwraca zainicjalizowaną instancję klienta OpenAI lub None jeśli brak klucza."""
    global _client
    if _client is None:
        api_key = Env.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if api_key and OpenAI:
            _client = OpenAI(api_key=api_key)
    return _client


async def ask_iris(question: str) -> str:
    """Zadaje pytanie sztucznej inteligencji z zachowaniem osobowości Iris."""
    if not question or not question.strip():
        return "Podaj pytanie, na które mam odpowiedzieć!"

    client = get_openai_client()
    if not client:
        return "⚠️ Moduł AI jest obecnie niedostępny (brak skonfigurowanego klucza OPENAI_API_KEY w pliku .env)."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": IRIS_PERSONALITY},
                {"role": "user", "content": question}
            ],
            max_tokens=500,
            temperature=0.7
        )

        reply = response.choices[0].message.content
        return reply if reply else "Nie udało się wygenerować odpowiedzi."

    except Exception as e:
        print(f"[AI ERROR] Błąd podczas komunikacji z API: {e}")
        return "✨ Przepraszam, wystąpił problem podczas przetwarzania Twojego zapytania przez AI."