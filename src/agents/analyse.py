from src.agents.base_agent import BaseAgent
import json
from src.tools.simple_rag_tool import SimpleRAG
from src.tools.agent_tools import talk_research, talk_synthesis
from src.prompt.read_prompt import prompt, system_prompt


class AnalysisAgent(BaseAgent):
    def __init__(self, name="Analysis", rag: SimpleRAG = None):
        self.system_prompt = system_prompt("analyse")
        self.rag = rag
        self.tools = [talk_research, talk_synthesis]

        super().__init__(name, self.system_prompt, tools=self.tools)


    def decide_action(self, message, context="", **kwargs):
        rag_response = self.rag.query(message) if self.rag else ""
        prompt_ = prompt("analyse").format(message=message, context=rag_response)
        analysis_result = self.model.chat(self.system_prompt, prompt_, callback=kwargs.get("callback"), session_id=kwargs.get("session_id"))
        return analysis_result
    
