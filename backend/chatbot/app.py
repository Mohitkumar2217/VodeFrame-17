# rag_api.py
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.vectorstore import FaissVectorStore
from src.data_loader import load_all_documents
from src.search import RAGSearch

app = FastAPI(title="MERASATHI RAG Chatbot API")

# CORS (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic endpoints: health, root (landing), docs redirect
@app.get("/health")
def health():
    return {"status": "ok", "service": "mdoner-rag", "uptime": True}

@app.get("/", response_class=HTMLResponse)
def root():
    # If you want a static index.html in ./static/index.html, uncomment the block below
    # and remove the inline HTML.
    #
    # from fastapi.staticfiles import StaticFiles
    # if not app.router.routes or '/static' not in [r.path for r in app.router.routes]:
    #     app.mount("/static", StaticFiles(directory="static"), name="static")
    # return RedirectResponse(url="/static/index.html")
    html = """
    <html>
      <head><title>MERASATHI RAG Chatbot API</title></head>
      <body>
        <h1>MERASATHI RAG Chatbot API</h1>
        <p>Interactive API docs: <a href="/docs">/docs (Swagger UI)</a></p>
        <p>Try POST /ask with JSON: {"query":"How do I upload a DPR?","top_k":3}</p>
        <p>Health: <a href="/health">/health</a></p>
      </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)

# Initialize FAISS store 
persist_dir = "faiss_store"
faiss_path = os.path.join(persist_dir, "faiss.index")
meta_path = os.path.join(persist_dir, "metadata.pkl")

store = FaissVectorStore(persist_dir)

if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
    print("[INFO] FAISS store not found — building new index...")
    docs = load_all_documents("data")
    store.build_from_documents(docs)
    store.save()
    print("[INFO] Vectorstore created and saved.")
else:
    print("[INFO] FAISS store found — loading existing index...")
    store.load()
 
# Initialize RAGSearch 
rag_search = RAGSearch(persist_dir=persist_dir)
 
# Request model & endpoint 
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/ask")
def ask_portal(req: QueryRequest):
    try:
        resp = rag_search.search_and_summarize(req.query, top_k=req.top_k)
        return {"answer": resp}
    except Exception as e:
        # keep error details for logs; return friendly message to client
        print("[ERROR]", e)
        return JSONResponse(status_code=500, content={
            "error": "internal_error",
            "message": "An error occurred while processing the RAG search."
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
