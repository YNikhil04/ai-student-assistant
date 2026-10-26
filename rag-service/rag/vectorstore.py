"""ChromaDB vector store backed by Gemini embeddings (via LangChain)."""
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

import config

COLLECTION_NAME = "student_docs"

_embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
_store: Optional[Chroma] = None


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
        )
    return _embeddings


def get_store() -> Chroma:
    global _store
    if _store is None:
        _store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=config.CHROMA_DIR,
        )
    return _store


def add_chunks(chunks: List[Document], doc_id: str, filename: str) -> int:
    for i, chunk in enumerate(chunks):
        chunk.metadata["doc_id"] = doc_id
        chunk.metadata["filename"] = filename
        chunk.metadata["chunk_index"] = i

    store = get_store()
    ids = [f"{doc_id}-{i}" for i in range(len(chunks))]

    # Embed in small batches to stay inside API limits
    batch = 50
    for start in range(0, len(chunks), batch):
        store.add_documents(
            chunks[start : start + batch], ids=ids[start : start + batch]
        )
    return len(chunks)


def search(query: str, doc_id: str, k: int = config.TOP_K):
    """Return [(Document, relevance_score 0..1)] restricted to one document."""
    store = get_store()
    return store.similarity_search_with_relevance_scores(
        query, k=k, filter={"doc_id": doc_id}
    )


def delete_document(doc_id: str) -> None:
    get_store().delete(where={"doc_id": doc_id})
