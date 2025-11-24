import os

from langchain_core.messages import BaseMessage
# load dotenv
from dotenv import load_dotenv



class LLMWrapper:
    def __init__(self):
        load_dotenv()
        self.model_name = os.getenv("MODEL", "ollama").lower()
        if self.model_name.startswith("m"):
            from langchain_mistralai import ChatMistralAI
            self.model = ChatMistralAI(
                model=self.model_name,
                api_key=os.getenv("MISTRAL_API_KEY"),
                temperature=0
            )
        else:
            from langchain_ollama import ChatOllama
            self.model = ChatOllama(
                model=self.model_name,
                temperature=0
            )

    def chat(self, system_prompt, prompt):
        # Ici on peut ajouter comptage de tokens, logging, etc.
        response = self.model.invoke([
            ("system", system_prompt),
            ("human", prompt)
        ])
        return response.content