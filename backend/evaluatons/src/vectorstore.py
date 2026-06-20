import os
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

class FaissVectorStore:

    def __init__(self, persist_dir, model_name="all-MiniLM-L6-v2"):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)   # <--- IMPORTANT
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.metadata = []

    def safe_load(self):
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")

        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
            print("[WARN] FAISS index not found. Needs rebuild.")
            return False
        
        self.index = faiss.read_index(faiss_path)
        self.metadata = pickle.load(open(meta_path, "rb"))
        print("[INFO] FAISS index loaded successfully.")
        return True

    def build_from_documents(self, docs):
        texts = [d.page_content for d in docs]

        embeddings = self.model.encode(texts).astype("float32")
        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)

        self.metadata = [{"text": t} for t in texts]

    def save(self):
        os.makedirs(self.persist_dir, exist_ok=True)   # <--- ENSURE DIR EXISTS

        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")

        faiss.write_index(self.index, faiss_path)
        pickle.dump(self.metadata, open(meta_path, "wb"))

        print("[INFO] FAISS index saved.")

    def query(self, query_text, top_k=5):
        query_vec = self.model.encode([query_text]).astype("float32")
        D, I = self.index.search(query_vec, top_k)
        results = []
        for idx, dist in zip(I[0], D[0]):
            results.append({
                "metadata": self.metadata[idx],
                "distance": dist
            })
        return results
