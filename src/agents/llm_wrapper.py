import os
import time

from marshmallow.utils import timestamp
from langchain_core.callbacks import BaseCallbackHandler

from src.costs.cost_logger import CostLogger
# load dotenv
from dotenv import load_dotenv

class RealTimeCallbackHandler(BaseCallbackHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_tool_start(self, serialized, input_str, **kwargs):
        if self.callback:
            self.callback({
                "type": "tool_start",
                "tool": serialized.get("name"),
                "input": input_str
            })

    def on_tool_end(self, output, **kwargs):
        if self.callback:
            self.callback({
                "type": "tool_end",
                "output": str(output)
            })

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if self.callback:
            self.callback({
                "type": "thought",
                "content": token
            })



class LLMWrapper:
    def __init__(self, tools=None):
        load_dotenv()
        self.model_name = os.getenv("MODEL", "ollama").lower()
        self.logger = CostLogger()
        if self.model_name.startswith("m"):
            from langchain_mistralai import ChatMistralAI
            self.model = ChatMistralAI(
                model=self.model_name,
                api_key=os.getenv("MISTRAL_API_KEY"),
                temperature=0,
                streaming=True
            )
        else:
            from langchain_ollama import ChatOllama
            self.model = ChatOllama(
                model=self.model_name,
                temperature=0,
                streaming=True
            )
        self.tools = tools



    def count_tokens(self, text):
        return self.model.get_num_tokens(text)

    def chat(self, system_prompt, prompt, callback=None, session_id=None):
        # Ici on peut ajouter comptage de tokens, logging, etc.
        input_tokens = self.count_tokens(system_prompt) + self.count_tokens(prompt)
        t0 = time.time()
        if self.tools:
            from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.messages import AIMessage

            # Création d'un prompt template adapté aux agents
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])

            # Création de l'agent et de l'exécuteur
            agent = create_tool_calling_agent(self.model, self.tools, prompt_template)
            agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, return_intermediate_steps=True)

            # Setup callback handler
            callbacks = [RealTimeCallbackHandler(callback)] if callback else []

            try :
                print(prompt)
                # L'agent executor attend généralement une clé "input"
                response_dict = agent_executor.invoke(
                    {"input": prompt},
                    config={"callbacks": callbacks}
                )
                
                # On enveloppe la réponse textuelle dans un AIMessage pour garder la compatibilité avec le reste du code (.content)
                response = AIMessage(content=response_dict["output"])
                status = "success"
            except Exception as e :
                response = AIMessage(content=str(e))
                status = "error"
                raise e
        else :
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
            status=status,
            session_id=session_id
        )

        return response.content
