from src.agents.llm_wrapper import LLMWrapper
from uuid import uuid4
from datetime import datetime


class BaseAgent:
    def __init__(self, name, system_prompt):
        self.name = name
        self.id = str(uuid4())
        self.system_prompt = system_prompt
        self.model = LLMWrapper()
        self.memory = []  # pour un module mémoire simple
        self.tools = []  # liste des outils disponibles (API, DB, etc.)

    # Gestion d'un message utilisateur
    def handle_user_message(self, message):
        print(f"[{self.name}] Nouveau message utilisateur: {message}")
        response = self.decide_action(message, source="user")
        return response

    # Gestion d'un message provenant d'un autre agent
    def handle_agent_message(self, message, sender_agent):
        print(f"[{self.name}] Nouveau message de l'agent {sender_agent.name}: {message}")
        response = self.decide_action(message, source="agent", sender=sender_agent)
        return response

    # Fonction de prise de décision
    def decide_action(self, message, source="user", sender=None):
        """
        Ici on peut :
        - interroger un autre agent
        - appeler un outil/API
        - répondre directement à l'utilisateur
        """
        # Exemple générique : log + renvoyer une réponse simple
        self.memory.append({"source": source, "message": message, "time": datetime.now()})

        # Exemple simple d'appel LLM
        prompt = f"\nMessage reçu ({source}): {message}\nRéponse:"
        response = self.model.chat(self.system_prompt, prompt)
        return response

    # Optionnel : fonction pour appeler un outil externe
    def call_tool(self, tool_name, **kwargs):
        print(f"[{self.name}] Appel de l'outil {tool_name} avec {kwargs}")
        # Ici vous pouvez implémenter l'appel réel à l'API ou DB
        return f"Résultat simulé de {tool_name}"


# Exemple d'agent spécialisé
class AgentRecherche(BaseAgent):
    def decide_action(self, message, source="user", sender=None):
        # Exemple : recherche d'article scientifique
        result = self.call_tool("search_api", query=message)
        return result


class AgentSynthese(BaseAgent):
    def decide_action(self, message, source="user", sender=None):
        # Exemple : synthèse LLM
        prompt = f"{self.system_prompt}\nSynthétise ce contenu:\n{message}\nRésumé:"
        response = self.model.chat(prompt)
        return response

# Utilisation

if __name__ == "__main__":
    agent_recherche = AgentRecherche("Recherche", system_prompt="Tu es un agent de recherche scientifique.")
    agent_synthese = AgentSynthese("Synthèse", system_prompt="Tu es un agent de synthèse scientifique.")

    # Exemple d'interaction
    msg = "Trouve des articles récents sur l'IA en santé."
    search_result = agent_recherche.handle_user_message(msg)
    summary = agent_synthese.handle_user_message(search_result)

    print("Résultat recherche:", search_result)
    print("Résumé:", summary)
