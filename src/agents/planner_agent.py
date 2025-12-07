import json
from src.agents.base_agent import BaseAgent
from src.agents.fact_checker_agent import FactCheckerAgent
from src.agents.research_agent import ResearchAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.tools.simple_rag_tool import SimpleRAG


class PlannerAgent(BaseAgent):
    def __init__(self, name: str, research_agent: ResearchAgent, synthesis_agent: SynthesisAgent, fact_checker_agent: FactCheckerAgent):
        system_prompt = (
            "You are a Planner Agent. Your role is to analyze a user request and extract a clear, precise, and search-friendly scientific topic.\n"
            "Output ONLY the topic string, without any introductory text or formatting.\n"
            "Example:\n"
            "User: 'Tell me about the impact of climate change on polar bears.'\n"
            "Output: Impact of climate change on polar bear populations"
        )
        if research_agent is None or synthesis_agent is None or fact_checker_agent is None:
            raise ValueError("research_agent, synthesis_agent and fact_checker_agent must be provided")
        self.research_agent = research_agent
        self.synthesis_agent = synthesis_agent
        self.fact_checker_agent = fact_checker_agent
        super().__init__(name, system_prompt)

    def decide_action(self, message, progress_callback=None, **kwargs):
        # Step 1: Generate clear topic via LLM
        if progress_callback:
            progress_callback("Analyzing request and extracting topic...", 10)
        
        print(f"[{self.name}] Generating topic from message: {message}")
        topic = self.model.chat(self.system_prompt, f"Extract a search topic from this message: {message}")
        topic = topic.strip()
        print(f"[{self.name}] Extracted topic: {topic}")

        # Step 2: Send topic to Research Agent
        if progress_callback:
            progress_callback(f"Researching topic: {topic}...", 30)
            
        print(f"[{self.name}] Sending topic to ResearchAgent...")
        research_json_str = self.research_agent.handle_user_message(topic)
        try:
            articles_list = json.loads(research_json_str)
        except json.JSONDecodeError:
            print(f"[{self.name}] Error decoding research results. Using empty list.")
            articles_list = []

        # Step 3: Send to Synthesis Agent
        if progress_callback:
            progress_callback("Synthesizing information...", 60)
            
        synthesis_payload = json.dumps({
            "subject": topic,
            "articles": articles_list
        })
        print(f"[{self.name}] Sending data to SynthesisAgent...")
        synthesis_result = self.synthesis_agent.handle_user_message(synthesis_payload)

        # Step 4: Send to Fact-Checker Agent
        if progress_callback:
            progress_callback("Fact-checking and refining...", 80)
            
        fact_checker_payload = json.dumps({
            "subject": topic,
            "articles": articles_list,
            "synthesis": synthesis_result
        })
        print(f"[{self.name}] Sending data to FactCheckerAgent...")
        final_result = self.fact_checker_agent.handle_user_message(fact_checker_payload)

        # Step 5: Return final result to user
        if progress_callback:
            progress_callback("Finalizing response...", 100)

        return final_result

if __name__ == "__main__":
    research = ResearchAgent("Research")
    synthesis = SynthesisAgent("Synthesis")
    fact_checker = FactCheckerAgent("FactChecker")
    planner = PlannerAgent("Planner", research, synthesis, fact_checker)
    
    user_msg = "Quels sont les effets du changement climatique sur les ours polaires ?"
    print("User Message:", user_msg)
    response = planner.handle_user_message(user_msg)
    print("\nFinal Response:\n", response)