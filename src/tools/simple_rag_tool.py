from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()

class SimpleRAG:
    _instance = None

    @staticmethod
    def get_instance(llm=None, documents=None, embedding_model="mxbai-embed-large"):
        if SimpleRAG._instance is None:
            if llm is None:
                raise ValueError("LLM is required to initialize SimpleRAG")
            SimpleRAG._instance = SimpleRAG(llm, documents, embedding_model)
        return SimpleRAG._instance

    def __init__(self, llm, documents=None, embedding_model="mxbai-embed-large"):
        """
        llm : instance de ChatOllama (ton modèle LLM)
        documents : liste de langchain_core.documents.Document
        embedding_model : modèle d'embedding gratuit supporté par Ollama
                          ex : "nomic-embed-text", "mxbai-embed-large"
        """
        if documents is None:
            documents = []
        self.documents = [
            d if isinstance(d, Document)
            else Document(
                page_content=d.get("content", d.get("text", "")),
                metadata={k: v for k, v in d.items() if k not in ["content", "text"]}
            )
            for d in documents
        ]
        print(len(self.documents), "documents loaded into RAG.")
        # 1. Embeddings open-source (OllamaEmbed)
        ollama_host = os.getenv("OLLAMA_HOST")
        kwargs = {"model": embedding_model}
        if ollama_host:
            kwargs["base_url"] = ollama_host
            
        self.embeddings = OllamaEmbeddings(**kwargs)

        # 2. Indexation FAISS open-source
        self.vs = FAISS.from_documents(self.documents, self.embeddings)

        # 3. Retriever sur FAISS
        self.retriever = self.vs.as_retriever(search_kwargs={"k": 5})

        # 4. Prompt RAG
        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
            "You are a factual assistant.\n"
            "Use ONLY the retrieved context to answer.\n"
            "If the context is insufficient, reply: 'Not enough information'.\n\n"
            "Retrieved context:\n{context}"
            ),
            ("human", "{question}")
        ])

        self.llm = llm

        # 5. Pipeline RAG (graph / LCEL)
        self.chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
        )


    def add_documents(self, new_documents):
        new_docs = [
            d if isinstance(d, Document)
            else Document(
                page_content=d.get("content", d.get("text", "")),
                metadata={k: v for k, v in d.items() if k not in ["content", "text"]}
            )
            for d in new_documents
        ]
        self.vs.add_documents(new_docs)

    def search(self, question):
        """
        Retrieves relevant documents and returns the context string and a list of unique sources.
        """
        docs = self.retriever.invoke(question)
        context_parts = []
        sources = []
        seen_urls = set()
        
        for d in docs:
            url = d.metadata.get("source") or d.metadata.get("link") or "Unknown"
            title = d.metadata.get("name") or d.metadata.get("title") or "Unknown Source"
            
            if url not in seen_urls and url != "Unknown":
                sources.append({"title": title, "url": url})
                seen_urls.add(url)
                
            context_parts.append(f"Source: {url}\nTitle: {title}\nContent: {d.page_content}")
            
        context = "\n\n---\n\n".join(context_parts)
        return context, sources

    def query(self, question):
        return ""
        # return self.chain.invoke(question)
