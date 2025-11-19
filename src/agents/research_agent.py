from base_agent import BaseAgent
import json
import requests

class ResearchAgent(BaseAgent):
    def __init__(self, name="Research"):
        system_prompt = (
            "You are a highly efficient scientific research agent.\n"
            "Your task is to generate several relevant web queries from a given topic in order to broadly cover the subject.\n"
            "Queries should be concise and contain keywords.\n"
            "- Return a JSON in the form: {{\"queries\": [\"query1\", \"query2\", ...]}}\n"
            "- Verify the consistency and completeness of your JSON before returning it."
        )
        super().__init__(name, system_prompt)

    def generate_queries(self, topic):
        prompt = f"""
        For the following topic:
        {topic}
        Generate 5 to 10 relevant web queries to cover this topic exhaustively.
        Return a JSON in the form: {{"queries": ["query1", "query2", ...]}}
        """
        result = self.model.chat(self.system_prompt, prompt)
        try:
            # Find the start and end of the JSON
            start = result.find('{')
            end = result.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = result[start:end]
                queries_json = json.loads(json_str)
                return queries_json.get("queries", [])
        except Exception as e:
            print(f"JSON parsing error: {e}")

            # Simple fallback if parsing fails
        return [topic]

    def search_crossref(self, query, max_results=5):
        url = "https://api.crossref.org/works"
        params = {"query": query, "rows": max_results}

        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json().get("message", {}).get("items", [])
            articles = []

            for item in data:
                content = item.get("abstract", "").strip()
                no_abstract = content.lower() in ["", "(no abstract available)", "n/a", "none"]
                if no_abstract:
                    continue
                articles.append({
                    "name": item.get("title", ["Unknown"])[0],
                    "link": item.get("URL", "Unknown"),
                    "author": ", ".join(
                        [a.get("family", "") for a in item.get("author", [])]) if "author" in item else "Unknown",
                    "content": item.get("abstract", "(No abstract available)")
                })
            return articles

        except Exception as e:
            print(f"CrossRef error: {e}")
            return []

    def search_semantic_scholar(self, query, max_results=5):
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,url,authors,abstract"
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json().get("data", [])
            articles = []

            for item in data:
                content = item.get("abstract", "")
                if content is None or content.strip() == "":
                    continue

                articles.append({
                    "name": item.get("title", "Unknown"),
                    "link": item.get("url", "Unknown"),
                    "author": ", ".join(a.get("name") for a in item.get("authors", [])),
                    "content": item.get("abstract", "(No abstract available)")
                })
            return articles

        except Exception as e:
            print(f"Semantic Scholar error: {e}")
            return []

    def fetch_articles(self, queries, max_results=5):
        articles = []

        for q in queries:
            #articles.extend(self.search_crossref(q, max_results))
            articles.extend(self.search_semantic_scholar(q, max_results))

        return articles


    def decide_action(self, message, source="user", sender=None):
        # Here we process the request as a given topic
        queries = self.generate_queries(message)
        print(f"[{self.name}] Generated queries: {queries}\n\n\n")
        articles = self.fetch_articles(queries)
        return json.dumps(articles, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    research_agent = ResearchAgent()
    topic = "Impact of California wildfires"
    results = research_agent.handle_user_message(topic)
    print(json.dumps(results, indent=2, ensure_ascii=False))