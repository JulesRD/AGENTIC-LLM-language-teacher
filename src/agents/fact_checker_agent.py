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

    def __init__(self, rag: SimpleRAG, name, max_iterations=3):
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
        self.rag = rag
        self.max_iterations = max_iterations

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
                "Task: Improve the synthesis based on the context.\n"
                "- Correct any factual errors.\n"
                "- Remove contradictions.\n"
                "- Integrate missing citations if available in context.\n"
                "- Ensure the text flows well.\n"
                "IMPORTANT: Output ONLY the rewritten synthesis. Do not output a list of changes or a critique section. Do not repeat the 'SYNTHESIS' header."
            )
            current_summary = self.model.chat(self.system_prompt, prompt)
        return current_summary

    def decide_action(self, message):
        try:
            parsed = json.loads(message)
            if "subject" not in parsed or "synthesis" not in parsed:
                raise ValueError("Invalid input format")
        except Exception:
            return "ERROR: SynthesisAgent expected a JSON string containing 'subject' and 'synthesis'."

        topic = parsed.get("subject")
        synthesis = parsed.get("synthesis", "")

        # Perform fact-checking and improvement
        improved_summary = self.fact_check_synthesis(topic, synthesis)
        return improved_summary