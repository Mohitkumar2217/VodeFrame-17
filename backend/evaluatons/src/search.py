import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.vectorstore import FaissVectorStore
from src.web_search import duckduckgo_search

load_dotenv()

class RAGSearch:
    def __init__(self, persist_dir="dpr_faiss_store", embedding_model="all-MiniLM-L6-v2", llm_model="llama-3.3-70b-versatile"):
        self.persist_dir = persist_dir
        self.vectorstore = FaissVectorStore(persist_dir, embedding_model)

        loaded = self.vectorstore.safe_load()
        if not loaded:
            print("[INFO] FAISS index not loaded. Upload DPR first.")

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY")

        self.llm = ChatGroq(
            groq_api_key=api_key,
            model=llm_model,
            max_tokens=1500
        )

    def search_and_summarize(self, query: str, top_k: int = 5):
        if not self.vectorstore.index:
            return "No FAISS index. Upload a DPR first."

        results = self.vectorstore.query(query, top_k=top_k)
        dpr_context = "\n\n".join(
            r["metadata"].get("text", "")[:1500] for r in results
        )

        web_results = duckduckgo_search(query, max_results=3)
        web_context = "\n".join(web_results)

        prompt = f"""
            You are a DPR expert.
            
            ### DPR Context:
            {dpr_context}
            
            ### Web Validation:
            {web_context}
            
            ### Query:
            {query}
            
            Rules:
            - Use DPR content first.
            - Use web only for validation.
            - Short, structured answer.
            - Mark source: [DPR], [Web], or [Both].
            
            Answer:
            """
            
        res = self.llm.invoke([prompt])
        return res.content.strip()
