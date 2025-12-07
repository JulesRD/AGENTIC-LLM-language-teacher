import os
import time

from marshmallow.utils import timestamp

from src.costs.cost_logger import CostLogger
# load dotenv
from dotenv import load_dotenv



class LLMWrapper:
    def __init__(self):
        load_dotenv()
        self.model_name = os.getenv("MODEL", "ollama").lower()
        self.logger = CostLogger()

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

    def count_tokens(self, text):
        return self.model.get_num_tokens(text)

    def chat(self, system_prompt, prompt):
        # Ici on peut ajouter comptage de tokens, logging, etc.
        input_tokens = self.count_tokens(system_prompt) + self.count_tokens(prompt)
        t0 = time.time()

        try :
            response = self.model.invoke([
                ("system", system_prompt),
                ("human", prompt)
            ])
            status = "success"
        except Exception as e :
            response = str(e)
            status = "error"

        latency_ms = (time.time() - t0) * 1000
        output_tokens = self.count_tokens(response.content)

        # LOG AUTOMATIQUE
        self.logger.log(
            model=self.model_name,
            endpoint="chat",
            prompt=system_prompt + "\n" + prompt,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            latency_ms=latency_ms,
            status=status
        )

        return response.content
