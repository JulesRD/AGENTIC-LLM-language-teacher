from mistralai import Mistral
import os

api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("MISTRAL_API_KEY environment variable is not set")

with Mistral(
    api_key=api_key,
) as mistral:

    res = mistral.chat.complete(model="ministral-3b-latest", messages=[
        {
            "content": "Who is the best French painter? Answer in one short sentence.",
            "role": "user",
        },
    ], stream=False)

    # Extraire seulement le content de la réponse
    if res.choices and len(res.choices) > 0:
        content = res.choices[0].message.content
        print(content)
    else:
        print("Aucune réponse reçue")

