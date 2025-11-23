import json
from src.agents.base_agent import BaseAgent
from src.tools.simple_rag_tool import SimpleRAG


class FactCheckerAgent(BaseAgent):
    """
        Fact-Checker / Critique Agent

        Responsibilities:
        - Validate, correct, and criticize the synthesized summary.
        - Identify hallucinations, contradictions, semantic drift.
        - Suggest corrections, add missing citations, verify dates, numbers, and interpretations.
        - Return an annotated or cleaned version of the final synthesis.
    """

    def __init__(self, name, max_iterations=3):
        self.system_prompt = """
            You are a Fact-Checker agent. 
            Your task is to review scientific summaries and suggest improvements.
            You should detect :
            - hallucinations
            - contradictions
            - incorrect interpretations
            - missing citations
            - wrong dates or numbers
            Output a corrected and annotated summary highlighting uncertain points.
        """
        super().__init__(name, self.system_prompt)
        self.rag = None
        self.max_iterations = max_iterations

    def create_rag_tool(self, articles):
        self.rag = SimpleRAG(self.model.model, articles)

    def fact_check_synthesis(self, topic, synthesis):
        current_summary = synthesis
        for i in range(self.max_iterations):
            # 1. Interroger RAG
            context = self.rag.query(current_summary)

            # 2. Faire la critique
            prompt = (
                f"Iteration {i + 1}/{self.max_iterations}\n\n"
                f"SYNTHESIS:\n{current_summary}\n\n"
                f"RETRIEVED CONTEXT:\n{context}\n\n"
                "Improve the synthesis: correct errors, detect contradictions, "
                "add citations, flag uncertain areas."
            )
            current_summary = self.model.chat(self.system_prompt, prompt)
        return current_summary

    # Fonction de prise de décision
    def decide_action(self, message, source="user", sender=None):
        try:
            parsed = json.loads(message)
            if "subject" not in parsed or "articles" not in parsed or "synthesis" not in parsed:
                raise ValueError("Invalid input format")
        except Exception:
            return "ERROR: SynthesisAgent expected a JSON string containing 'topic' and 'articles'."

        topic = parsed.get("subject")
        articles = parsed.get("articles", [])
        synthesis = parsed.get("synthesis", "")

        # Initialize RAG tool with articles
        self.create_rag_tool(articles)

        # Perform fact-checking and improvement
        improved_summary = self.fact_check_synthesis(topic, synthesis)
        return improved_summary



# Usage example
if __name__ == "__main__":
    agent_fact_checker = FactCheckerAgent("Fact-Checker", max_iterations=2)

    # Example interaction
    msg = json.dumps({
        "subject": "AI in Healthcare",
        "articles": [
            {
                "name": "Article 1",
                "author": "Author A",
                "link": "http://example.com/article1",
                "content": "This article reviews the recent advances in AI applications in healthcare..."
            },
            {
                "name": "Article 2",
                "author": "Author B",
                "link": "http://example.com/article2",
                "content": "Machine learning techniques have shown promise in improving medical diagnosis accuracy..."
            }
        ],
        "synthesis": "The synthesized summary states that AI has revolutionized healthcare by improving diagnostics and treatment plans. However, some claims lack proper citations and there are inconsistencies regarding the timeline of AI advancements."
    })

    fact_checked_summary = agent_fact_checker.handle_user_message(msg)
    print("Fact-Checked Summary:\n", fact_checked_summary)