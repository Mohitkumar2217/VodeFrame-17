from langchain_community.document_loaders import PyPDFLoader

def load_dpr_pdf(path):
    try:
        loader = PyPDFLoader(path)
        return loader.load()
    except Exception:
        return []
