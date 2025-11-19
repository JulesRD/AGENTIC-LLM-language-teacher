import json
from base_agent import BaseAgent


class SynthesisAgent(BaseAgent):
    """
        Agent responsible for:
        1) Summarizing each article individually using the LLM.
        2) Synthesizing all summaries into a final structured answer.
        """

    def __init__(self, name):
        self.system_prompt = """
        You are a scientific synthesis agent.
        Your task is to summarize and synthesize information from scientific articles.
        Do not introduce any new information not present in the articles.
        """
        super().__init__(name, self.system_prompt)

    def summarize_article(self, topic, article):
        content = article.get("content", "")
        prompt = f"""
        Summarize the following article in a few sentences (2-3), focusing on the most important points.:
        It should be relevant to the topic: {topic}
        Do not add any additional information not present in the article.
        Title: {article.get("name", "Unknown")}
        Author(s): {article.get("author", "Unknown")}
        Link: {article.get("link", "Unknown")}
        Content: {content}
        Summary:
        """
        return self.model.chat(self.system_prompt, prompt)

    def synthesize_summaries(self, topic, summaries):
        prompt = f"""
        You are a scientific synthesis agent.
        Given the following summaries of articles related to the topic '{topic}', synthesize them into a coherent and structured final answer.
        Ensure that the final synthesis covers all key points from the individual summaries.
        Do not introduce any new information.
        Here are the summaries:
        """
        for summary in summaries:
            prompt += f"\nTitle: {summary['title']}\nSummary: {summary['summary']}\n"
        prompt += "\nFinal Synthesis:"
        return self.model.chat(self.system_prompt, prompt)

    # Fonction de prise de décision
    def decide_action(self, message, source="user", sender=None):
        try:
            parsed = json.loads(message)
            if "subject" not in parsed or "articles" not in parsed:
                raise ValueError("Invalid input format")
        except Exception:
            return "ERROR: SynthesisAgent expected a JSON string containing 'topic' and 'articles'."

        topic = parsed.get("subject")
        articles = parsed.get("articles", [])

        # Summarize each article individually
        individual_summaries = []
        for article in articles:
            summary = self.summarize_article(topic, article)
            individual_summaries.append({
                "title": article.get("name", "Unknown"),
                "summary": summary
            })

        # Synthesize all summaries into a final answer
        final_synthesis = self.synthesize_summaries(topic, individual_summaries)
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