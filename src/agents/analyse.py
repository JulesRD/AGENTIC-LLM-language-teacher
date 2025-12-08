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
        context_str = ""
        sources = []
        callback = kwargs.get("callback")
        
        if self.rag:
            if callback:
                callback({"type": "status", "status": "Searching knowledge base...", "source_count": 0})
            
            context_str, sources = self.rag.search(message)
            
            if callback:
                callback({"type": "status", "status": "Analyzing...", "source_count": len(sources)})

        prompt_ = prompt("analyse").format(message=message, context=context_str)
        analysis_result = self.model.chat(
            self.system_prompt, 
            prompt_, 
            callback=callback, 
            session_id=kwargs.get("session_id"),
            max_iterations=kwargs.get("max_iterations", 15),
            stop_event=kwargs.get("stop_event")
        )
        
        # Return a dict instead of string to pass sources separately
        return {
            "content": analysis_result,
            "sources": sources
        }
    
