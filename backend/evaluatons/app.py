import os
import uvicorn
import json
import traceback
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.vectorstore import FaissVectorStore
from src.dpr_loader import load_dpr_pdf
from src.search import RAGSearch
from src.evaluation import DPRAssistant
from src.web_search import duckduckgo_search

load_dotenv()
 
# ENSURE DIRECTORIES EXIST BEFORE MOUNTING 
CORE_DIRS = [
    "uploads",
    "annotated",
    "dpr_faiss_store",
    "evaluations/history"
]

for folder in CORE_DIRS:
    os.makedirs(folder, exist_ok=True)

# Resolve paths from current project directory (cross-platform)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GIS_DIR = os.path.join(BASE_DIR, "gis_outputs")
RISK_DIR = os.path.join(BASE_DIR, "risk_output")

os.makedirs(GIS_DIR, exist_ok=True)
os.makedirs(RISK_DIR, exist_ok=True)
 
# INIT FASTAPI 
app = FastAPI(title="Advanced DPR Intelligence API")
 
# STATIC FILE ROUTES 
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/annotated", StaticFiles(directory="annotated"), name="annotated")

# Mount GIS + Risk directories
app.mount("/gis_outputs", StaticFiles(directory=GIS_DIR), name="gis_outputs")
app.mount("/risk_output", StaticFiles(directory=RISK_DIR), name="risk_output")
 
# CORS CONFIG 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
 
# FAISS + RAG + AI ASSISTANT SETUP 
PERSIST_DIR = "dpr_faiss_store"

store = FaissVectorStore(PERSIST_DIR)
rag = RAGSearch(persist_dir=PERSIST_DIR)

dpr_eval = DPRAssistant()

# HELPER — Save Evaluation in JSON File 
def save_evaluation_json(pdf_name: str, evaluation_data: dict):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = pdf_name.replace(".pdf", "").replace(" ", "_")
    filename = f"evaluations/history/{safe_name}_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(evaluation_data, f, indent=2, ensure_ascii=False)

    return filename

# 1. UPLOAD + PROCESS + EVALUATE DPR 
@app.post("/upload_dpr")
async def upload_dpr(file: UploadFile = File(...)):
    try: 
        # SAVE THE PDF 
        save_path = os.path.join("uploads", file.filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())

        print(f"[INFO] PDF saved → {save_path}")
 
        # PARSE PDF TEXT 
        docs = load_dpr_pdf(save_path)
        if not docs:
            return {"error": "Failed to extract text from PDF"}

        dpr_text = "\n\n".join([d.page_content for d in docs])

        # Build FAISS
        store.build_from_documents(docs)
        store.save()
        rag.vectorstore = store

        dpr_eval.input_pdf_path = save_path
 
        # RUN FULL EVALUATION PIPELINE 
        result = dpr_eval.evaluate(dpr_text)
 
        # SAVE JSON OUTPUT 
        output_file = save_evaluation_json(file.filename, result)
        print(f"[INFO] AI Evaluation Saved → {output_file}")
 
        # RETURN RESPONSE TO FRONTEND 
        return {
            "status": "success",
            "evaluation": result["report"],
            "issues": result["issues"],
            "highlighted_pdf": result["highlighted_pdf"],
            "saved_json": output_file
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

# 2. LIST GIS IMAGES 
@app.get("/gis_images")
def list_gis_images():
    folder = GIS_DIR
    try:
        files = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}


@app.get("/risk_images")
def list_risk_images():
    folder = RISK_DIR
    try:
        files = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}


# 4. RAG QUERY 
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/ask")
def ask(req: QueryRequest):
    try:
        answer = rag.search_and_summarize(req.query, top_k=req.top_k)
        return {"answer": answer}
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
 
# 5. SEARCH WEB 
@app.get("/search_web")
def search_web(q: str):
    try:
        return {"query": q, "results": duckduckgo_search(q)}
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

 
# 6. REEVALUATE WITHOUT RE-UPLOAD 
@app.post("/evaluate_dpr")
def reevaluate():
    try:
        store.safe_load()
        if not store.metadata:
            return {"error": "Upload a DPR first"}

        dpr_text = "\n\n".join([m["text"] for m in store.metadata])

        if not dpr_eval.input_pdf_path:
            return {"error": "Original PDF missing. Upload again."}

        result = dpr_eval.evaluate(dpr_text)

        return {
            "evaluation": result["report"],
            "issues": result["issues"],
            "highlighted_pdf": result["highlighted_pdf"],
        }

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
 
# 7. HEALTH CHECK 
@app.get("/health")
def health():
    return {"status": "running"}

 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
