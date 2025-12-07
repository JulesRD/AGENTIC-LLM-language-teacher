from src.agents.base_agent import BaseAgent
import json
import requests
from src.tools.simple_rag_tool import SimpleRAG

class ResearchAgent(BaseAgent):
    def __init__(self, rag: SimpleRAG, name="Research"):
        system_prompt = (
            "You are a highly efficient scientific research agent.\n"
            "Your task is to generate several relevant web queries from a given topic in order to broadly cover the subject.\n"
            "Queries should be concise and contain keywords.\n"
            "- Return a JSON in the form: {{\"queries\": [\"query1\", \"query2\", ...]}}\n"
            "- Verify the consistency and completeness of your JSON before returning it."
        )
        super().__init__(name, system_prompt)
        self.rag = rag

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

    def add_articles_to_rag(self, articles):
        # This method can be used to add articles to a RAG tool if needed
        self.rag.add_documents(articles)

    def decide_action(self, message, source="user", sender=None):
        # Here we process the request as a given topic
        queries = self.generate_queries(message)
        articles = self.fetch_articles(queries)
        self.add_articles_to_rag(articles)
        return json.dumps(articles, ensure_ascii=False, indent=2)