from src.agents.llm_wrapper import LLMWrapper
from uuid import uuid4


class BaseAgent:
    """
    Base agent class that provides core functionality for all specialized agents.
    Handles user messages and provides a decision-making interface through the decide_action method.
    """
    
    def __init__(self, name, system_prompt):
        self.name = name
        self.id = str(uuid4())
        self.system_prompt = system_prompt
        self.model = LLMWrapper()

    def handle_user_message(self, message):
        """
        Process a message from the user and return a response.
        
        Args:
            message: The user's input message
            
        Returns:
            The agent's response
        """
        print(f"[{self.name}] Processing user message: {message}")
        response = self.decide_action(message)
        return response

    def decide_action(self, message):
        """
        Core decision-making method to be overridden by specialized agents.
        Default implementation uses the LLM to generate a response.
        
        Args:
            message: The input message to process
            
        Returns:
            The agent's response
        """
        prompt = f"\nReceived message: {message}\nResponse:"
        response = self.model.chat(self.system_prompt, prompt)
        return response
