import os
from openai import OpenAI
from core.personality import IRIS_PERSONALITY

_client = None
_provider = None  # "openai" or "gemini"
_model = None


def get_client_and_model():
    global _client, _provider, _model
    if _client is not None:
        return _client, _provider, _model

    # Pobieranie kluczy z pliku .env
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    # Jeśli klucz OPENAI_API_KEY zaczyna się od AIzaSy, traktujemy go jako klucz Gemini
    if openai_key and (openai_key.startswith("AIzaSy") or "google" in openai_key.lower()):
        gemini_key = openai_key
        openai_key = None

    if gemini_key:
        # Korzystamy z oficjalnego i bezpłatnego punktu końcowego kompatybilnego z OpenAI dla Gemini
        _client = OpenAI(
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        _provider = "gemini"
        _model = "gemini-3.5-flash"
        print(f"Iris AI: Wykryto klucz Gemini. Uruchamiam Google Gemini ({_model}).")
    elif openai_key:
        _client = OpenAI(
            api_key=openai_key
        )
        _provider = "openai"
        _model = "gpt-4o-mini"
        print(f"Iris AI: Wykryto klucz OpenAI. Uruchamiam OpenAI ({_model}).")
    else:
        _client = None
        _provider = None
        _model = None

    return _client, _provider, _model


async def ask_iris(question):
    print("Otrzymano pytanie do Iris:", question)
    if not question or not question.strip():
        return "Zadaj mi jakieś pytanie!"

    client, provider, model = get_client_and_model()

    if not client:
        return "⚠️ Moduł AI jest obecnie niedostępny. Skonfiguruj klucz `GEMINI_API_KEY` lub `OPENAI_API_KEY` w pliku .env bota."

    try:
        # Standardowa metoda kompatybilna ze wszystkimi nowoczesnymi wersjami SDK OpenAI
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": IRIS_PERSONALITY},
                {"role": "user", "content": question}
            ]
        )

        answer = response.choices[0].message.content
        print(f"Odpowiedź AI ({provider}):", answer)
        return answer

    except Exception as e:
        print(f"BŁĄD AI ({provider}):", e)
        error_str = str(e)
        if "401" in error_str or "invalid" in error_str.lower():
            return "⚠️ Nieprawidłowy klucz API. Upewnij się, że podany klucz w pliku .env jest poprawny dla wybranego dostawcy (OpenAI lub Gemini)."
        return f"Wystąpił błąd podczas komunikacji z AI bota: {e}"