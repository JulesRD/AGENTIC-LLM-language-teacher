from langchain_core.tools import tool
from src.agents.research_agent import ResearchAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.tools.simple_rag_tool import SimpleRAG

@tool
def talk_research(request: str) -> str:
    """Ask the research agent a question, he will request web searches"""
    research_agent = ResearchAgent(SimpleRAG.get_instance())
    print("research_agent initialized")
    return research_agent.decide_action(request)
    # print("Les agents sont en maintenance, veuillez réessayer plus tard.")
    # return "Les agents sont en maintenance, veuillez réessayer plus tard."

@tool
def talk_synthesis(data: str) -> str:
    """
    Ask the synthesis agent to summarize and synthesize information from scientific articles.
    Input 'data' MUST be a JSON string with the following structure:
    {
        "topic": "The topic of the synthesis",
        "articles": [
            {
                "name": "Article Title",
                "content": "Article content or abstract...",
                "author": "Author Name",
                "link": "URL"
            },
            ...
        ]
    }
    """
    synthesis_agent = SynthesisAgent(SimpleRAG.get_instance(), name="Synthesis")
    print("synthesis_agent initialized")
    return synthesis_agent.decide_action(data)
    # print("Les agents sont en maintenance, veuillez réessayer plus tard.")
    # return "Les agents sont en maintenance, veuillez réessayer plus tard."