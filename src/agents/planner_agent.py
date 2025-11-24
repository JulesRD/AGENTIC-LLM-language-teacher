from src.agents.base_agent import BaseAgent
from src.agents.fact_checker_agent import FactCheckerAgent
from src.agents.research_agent import ResearchAgent
from src.agents.synthesis_agent import SynthesisAgent


class PlannerAgent(BaseAgent):
    def __init__(self, name: str, research_agent: ResearchAgent, synthesis_agent: SynthesisAgent, fact_checker_agent: FactCheckerAgent):
        system_prompt = (
            #TODO
        )
        if research_agent is None or synthesis_agent is None or fact_checker_agent is None:
            raise ValueError("research_agent, synthesis_agent and fact_checker_agent must be provided")
        self.research_agent = research_agent
        self.synthesis_agent = synthesis_agent
        self.fact_checker_agent = fact_checker_agent
        super().__init__(name, system_prompt)

    def decide_action(self, message):
        # TODO
        # Step 1: Generate clear topic via LLM

        # Step 2: Send topic to Research Agent

        # Step 3: Send to Synthesis Agent

        # Step 4: Send to Fact-Checker Agent

        # Step 5: Return final result to user
        pass

if __name__ == "__main__":
    # TODO
    pass