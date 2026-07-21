import os
from openai import OpenAI
from core.personality import IRIS_PERSONALITY

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


async def ask_iris(question):
    print("Otrzymano pytanie:", question)

    try:
        response = client.responses.create(
            model="gpt-5-mini",
            instructions=IRIS_PERSONALITY,
            input=question
        )

        print("Odpowiedź AI:", response.output_text)

        return response.output_text

    except Exception as e:
        print("BŁĄD AI:", e)
        return "Wystąpił błąd podczas łączenia z AI."