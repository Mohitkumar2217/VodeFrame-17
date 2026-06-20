import os
from dotenv import load_dotenv
from src.vectorstore import FaissVectorStore
from langchain_groq import ChatGroq

load_dotenv()

class RAGSearch:
    def __init__(
        self,
        persist_dir: str = "faiss_store",
        embedding_model: str = "all-MiniLM-L6-v2",
        llm_model: str = "llama-3.1-8b-instant"
    ):
        self.vectorstore = FaissVectorStore(persist_dir, embedding_model)

        # Load or build vectorstore
        faiss_path = os.path.join(persist_dir, "faiss.index")
        meta_path = os.path.join(persist_dir, "metadata.pkl")

        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
            print("[INFO] FAISS store missing, rebuilding...")
            from src.data_loader import load_all_documents
            docs = load_all_documents("data")
            self.vectorstore.build_from_documents(docs)
        else:
            self.vectorstore.load()

        groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=llm_model)
        print(f"[INFO] Groq LLM initialized: {llm_model}")
 
    def search_and_summarize(self, user_query: str, top_k: int = 5) -> str:

        # Retrieve chunks from FAISS
        results = self.vectorstore.query(user_query, top_k=top_k)

        guide_context = "\n\n".join([
            r["metadata"].get("text", "")
            for r in results
            if r["metadata"]
        ])

        if not guide_context.strip():
            return (
                "No relevant information was found in the portal guide.\n"
                "Please try rephrasing your question."
            )
 
        prompt = f"""
You are an **official MDONER Portal Assistant**, trained to answer questions strictly using the provided context.
Your job is to help users (students, teachers, admins, ministries) with correct and policy-based information.

### 📘 CONTEXT (Highly Relevant Extracts)
{guide_context}

### 💬 USER QUESTION
{user_query}

### 🧠 RULES — You MUST follow:
1. Only answer using information from the context above.  
2. If something is not in the context, say:  
   **"This detail is not mentioned in the MDONER portal guide."**
3. Use clean formatting with real line breaks.  
4. Use numbered points, bullet points, and clear structure.  
5. Keep tone formal, helpful, and precise.  
6. No assumptions. No external knowledge.

### ✅ FINAL ANSWER FORMAT
- Start directly with the solution.
- Use neat bullet points or numbered steps.
- No unnecessary text.

Now provide the final answer:
"""

        # Call LLM
        response = self.llm.invoke([prompt])

        # Clean result
        answer = response.content.strip()
        return answer
 
if __name__ == "__main__":
    rag = RAGSearch()
  
