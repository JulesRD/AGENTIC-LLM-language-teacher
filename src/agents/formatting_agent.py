from src.agents.base_agent import BaseAgent
from src.prompt.read_prompt import prompt, system_prompt
import json

class FormattingAgent(BaseAgent):
    def __init__(self, name="Formatting"):
        self.system_prompt = system_prompt("formatting")
        super().__init__(name, self.system_prompt)

    def format_response(self, text, available_sources):
        """
        Formats the text and selects used sources.
        Returns a tuple (formatted_text, used_sources_list)
        """
        sources_str = json.dumps(available_sources, indent=2)
        prompt_content = prompt("formatting").format(
            text=text,
            sources=sources_str
        )
        
        response = self.model.chat(self.system_prompt, prompt_content)
        
        # Extract JSON block
        formatted_text = response
        used_sources = []
        
        try:
            if "```json" in response:
                parts = response.split("```json")
                formatted_text = parts[0].strip()
                json_str = parts[1].split("```")[0].strip()
                data = json.loads(json_str)
                used_sources = data.get("sources", [])
            elif "```" in response: # Fallback if user forgets 'json'
                parts = response.split("```")
                formatted_text = parts[0].strip()
                # Try to find the last block
                json_str = parts[-2].strip() 
                data = json.loads(json_str)
                used_sources = data.get("sources", [])
        except Exception as e:
            print(f"Error parsing formatting agent response: {e}")
            # Fallback: use all available sources if parsing fails
            used_sources = available_sources

        return formatted_text, used_sources
