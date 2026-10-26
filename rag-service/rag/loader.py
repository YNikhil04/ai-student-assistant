"""Load uploaded files into LangChain Document objects."""
from pathlib import Path
from typing import List

from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document


def load_document(path: str) -> List[Document]:
    ext = Path(path).suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(path)
    elif ext in {".txt", ".md"}:
        loader = TextLoader(path, encoding="utf-8", autodetect_encoding=True)
    elif ext == ".docx":
        loader = Docx2txtLoader(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return loader.load()
