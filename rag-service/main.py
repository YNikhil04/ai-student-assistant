import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import config
from rag import qa, vectorstore
from rag.chunker import chunk_documents
from rag.loader import load_document

app = FastAPI(title="AI Student Assistant - RAG Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CLIENT_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    doc_id: str
    question: str = Field(min_length=1, max_length=2000)


@app.get("/health")
def health():
    return {"status": "ok", "gemini_key_set": bool(config.GOOGLE_API_KEY)}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file type '{ext}'. Allowed: "
            f"{', '.join(sorted(config.ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    if len(content) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File larger than {config.MAX_UPLOAD_MB} MB.")

    doc_id = uuid.uuid4().hex
    save_path = os.path.join(config.UPLOAD_DIR, f"{doc_id}{ext}")
    with open(save_path, "wb") as f:
        f.write(content)

    try:
        docs = load_document(save_path)
        chunks = chunk_documents(docs)
        if not chunks:
            raise HTTPException(
                422,
                "No readable text found. Scanned/image-only PDFs need OCR first.",
            )
        count = vectorstore.add_chunks(chunks, doc_id, file.filename)
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Failed to process document: {e}")
    finally:
        # Raw file is no longer needed once it is embedded
        if os.path.exists(save_path):
            os.remove(save_path)

    return {"doc_id": doc_id, "filename": file.filename, "chunks": count}


@app.post("/ask")
def ask(req: AskRequest):
    try:
        return qa.answer_question(req.question, req.doc_id)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Failed to answer: {e}")


@app.delete("/document/{doc_id}")
def delete_document(doc_id: str):
    vectorstore.delete_document(doc_id)
    return {"deleted": doc_id}
