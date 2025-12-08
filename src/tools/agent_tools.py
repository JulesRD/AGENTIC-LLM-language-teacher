from langchain_core.tools import tool
from src.agents.research_agent import ResearchAgent
from src.agents.synthesis_agent import SynthesisAgent
@tool
def talk_research(request: str) -> str:
    """Ask the research agent a question, he will request web searches"""
    # research_agent = ResearchAgent()
    # return research_agent.decide_action(request)
    print("Les agents sont en maintenance, veuillez réessayer plus tard.")
    return "Les agents sont en maintenance, veuillez réessayer plus tard."

@tool
def talk_synthesis(data: str) -> str:
    """Ask the synthesis agent to summarize and synthesize information from scientific articles."""
    # synthesis_agent = SynthesisAgent()
    # return synthesis_agent.decide_action(data)
    print("Les agents sont en maintenance, veuillez réessayer plus tard.")
    return "Les agents sont en maintenance, veuillez réessayer plus tard."