from src.agents.llm_wrapper import LLMWrapper
from uuid import uuid4


class BaseAgent:
    """
    Base agent class that provides core functionality for all specialized agents.
    Handles user messages and provides a decision-making interface through the decide_action method.
    """
    
    def __init__(self, name, system_prompt, tools=None):
        self.name = name
        self.id = str(uuid4())
        self.system_prompt = system_prompt
        self.model = LLMWrapper(tools=tools)

    def handle_user_message(self, message, **kwargs):
        """
        Process a message from the user and return a response.
        
        Args:
            message: The user's input message
            **kwargs: Additional arguments to pass to decide_action
            
        Returns:
            The agent's response
        """
        
        print(f"[{self.name}] Processing user message: {message[:50]}...")
        response = self.decide_action(message, **kwargs)
        return response

    def decide_action(self, message, **kwargs):
        """
        Core decision-making method to be overridden by specialized agents.
        Default implementation uses the LLM to generate a response.
        
        Args:
            message: The input message to process
            **kwargs: Additional arguments
            
        Returns:
            The agent's response
        """
        prompt = f"\nReceived message: {message}\nResponse:"
        response = self.model.chat(self.system_prompt, prompt, callback=kwargs.get("callback"), session_id=kwargs.get("session_id"))
        return response

