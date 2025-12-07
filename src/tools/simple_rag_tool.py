from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document


class SimpleRAG:
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
        # 1. Embeddings open-source (OllamaEmbed)
        self.embeddings = OllamaEmbeddings(model=embedding_model)

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

    def query(self, question):
        return self.chain.invoke(question)
