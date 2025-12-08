import json
from src.agents.base_agent import BaseAgent
from src.tools.simple_rag_tool import SimpleRAG

from src.prompt.read_prompt import prompt, system_prompt


class SynthesisAgent(BaseAgent):
    """
        Agent responsible for:
        1) Summarizing each article individually using the LLM.
        2) Synthesizing all summaries into a final structured answer.
        """

    def __init__(self, rag: SimpleRAG, name):
        self.system_prompt = system_prompt("synthese")
        super().__init__(name, self.system_prompt)
        self.rag = rag

    def summarize_article(self, topic, article, user_request=""):
        content = article.get("content", "")
        self.prompt = prompt("synthese").format(
            article=article,
            content=content,
            topic=topic,
            user_request=user_request,
            title=article.get("name", "Unknown"),
            author=article.get("author", "Unknown"),
            link=article.get("link", "Unknown")
            
            )
        return self.model.chat(self.system_prompt, self.prompt)

    def synthesize_summaries(self, topic, summaries, user_request=""):
        prompt = f"""
        You are a scientific synthesis agent.
        Given the following summaries of articles related to the topic '{topic}', synthesize them into a coherent and structured final answer.
        The synthesis must specifically address the user's request: "{user_request}"
        Ensure that the final synthesis covers all key points from the individual summaries.
        Do not introduce any new information.
        Here are the summaries:
        """
        for summary in summaries:
            prompt += f"\nTitle: {summary['title']}\nSummary: {summary['summary']}\n"
        prompt += "\nFinal Synthesis:"
        return self.model.chat(self.system_prompt, prompt)

    def decide_action(self, message):
        try:
            parsed = json.loads(message)
            # Allow 'topic' or 'subject'
            topic = parsed.get("subject") or parsed.get("topic")
            user_request = parsed.get("user_request", "")
            if not topic or "articles" not in parsed:
                raise ValueError("Invalid input format")
        except Exception:
            return "ERROR: SynthesisAgent expected a JSON string containing 'topic' (or 'subject') and 'articles'."

        articles = parsed.get("articles", [])

        # Summarize each article individually
        individual_summaries = []
        for article in articles:
            summary = self.summarize_article(topic, article, user_request)
            individual_summaries.append({
                "title": article.get("name", "Unknown"),
                "summary": summary
            })

        # Synthesize all summaries into a final answer
        final_synthesis = self.synthesize_summaries(topic, individual_summaries, user_request)
        return final_synthesis

# Usage example
if __name__ == "__main__":
    synthesis_agent = SynthesisAgent("Synthesis")
    # Example input message
    example_message = json.dumps({
        "subject": "Recent advances in AI for healthcare",
        "articles": [
            {
                "name": "AI in Healthcare: A Review",
                "link": "http://example.com/ai-healthcare",
                "author": "John Doe",
                "content": "This article reviews the recent advances in AI applications in healthcare..."
            },
            {
                "name": "Machine Learning for Medical Diagnosis",
                "link": "http://example.com/ml-diagnosis",
                "author": "Jane Smith",
                "content": "Machine learning techniques have shown promise in improving medical diagnosis accuracy..."
            }
        ]
    })
    synthesis = synthesis_agent.handle_user_message(example_message)
    print("Final Synthesis:\n", synthesis)