from pathlib import Path
from typing import List, Any
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain_community.document_loaders import JSONLoader

def load_all_documents(data_dir: str) -> List[Any]:
    data_path = Path(data_dir).resolve()
    print(f"[DEBUG] Data path; {data_path}")
    documents = []

    #PDF
    pdf_files = list[Path](data_path.glob('**/*.pdf'))
    for pdf_file in pdf_files:
        try:
            loader = PyPDFLoader(str(pdf_file))
            loaded = loader.load()
            documents.extend(loaded)
        except Exception as e:
            print(f"[Error] Failed loading PDF {pdf_file} : {e}")

    #TXT 
    txt_files = list[Path](data_path.glob('**/*.txt'))
    for txt_file in txt_files:
        try:
            loader = TextLoader(str(txt_file))
            documents.extend(loader.load())
        except Exception as e:
            print(f"[ERROR] Failed TXT {txt_file} : {e}")

    #Excel
    xlsx_files = list[Path](data_path.glob('**/*.xlsx'))
    for xlsx_file in xlsx_files:
        try:
            loader = UnstructuredExcelLoader(str(xlsx_file))
            documents.extend(loader.load())
        except Exception as e:
            print(f"[ERROR] Failed Excel {xlsx_file}: {e}")

    # DOCX
    docx_files = list(data_path.glob('**/*.docx'))
    for docx_file in docx_files:
        try:
            loader = Docx2txtLoader(str(docx_file))
            documents.extend(loader.load())
        except Exception as e:
            print(f"[ERROR] Failed DOCX {docx_file}: {e}")

    # JSON
    json_files = list(data_path.glob('**/*.json'))
    for json_file in json_files:
        try:
            loader = JSONLoader(str(json_file))
            documents.extend(loader.load())
        except Exception as e:
            print(f"[ERROR] Failed JSON {json_file}: {e}")

    print(f"[DEBUG] Total loaded docs: {len(documents)}")
    return documents

# NEW:load_single_pdf() for DPR load
def load_single_pdf(pdf_path: str):
    """
    Load a single DPR PDF and return LangChain documents.
    """

    try:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        print(f"[INFO] Loaded {len(docs)} PDF pages from {pdf_path}")
        return docs
    except Exception as e:
        print(f"[ERROR] Single PDF Load Failed {pdf_path} : {e}")
        return []