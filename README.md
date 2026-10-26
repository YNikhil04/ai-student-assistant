# 📚 AI Student Assistant

A RAG (Retrieval-Augmented Generation) study assistant. Upload a PDF, DOCX or text file, ask a question in plain English, and get an answer grounded **only** in your document, with the source passages shown.

## How it works

```
React (5173)  ──►  Express gateway (5000)  ──►  FastAPI RAG service (8000)
  upload + ask        validates, forwards         LangChain + Gemini + ChromaDB
```

**Upload:** file → text extraction → chunking (1000 chars, 200 overlap) → Gemini embeddings → stored in ChromaDB tagged with a `doc_id`.

**Ask:** question → embedded → top-K similar chunks retrieved (only from that document) → chunks below a relevance threshold are discarded → Gemini answers from the remaining context → answer + sources returned.

### How it reduces hallucination
- The prompt tells Gemini to use **only** the retrieved context.
- If nothing relevant is retrieved, the app replies "I couldn't find this in the uploaded document" without calling the LLM.
- Low temperature (0.1).
- Source snippets and page numbers are shown so answers can be verified.

## Setup

You need Node 18+, Python 3.10+ and a free Gemini API key from https://aistudio.google.com/apikey

### 1. RAG service (FastAPI)
```bash
cd rag-service
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste your GOOGLE_API_KEY
uvicorn main:app --reload --port 8000
```

### 2. Gateway (Express)
```bash
cd server
npm install
cp .env.example .env
npm run dev
```

### 3. Frontend (React + Vite)
```bash
cd client
npm install
npm run dev
```

Open http://localhost:5173, upload a document, ask a question.

## Project structure
```
ai-student-assistant/
├── client/                 React UI (Vite)
│   └── src/ App.jsx, api.js, App.css
├── server/                 Express gateway
│   └── index.js
└── rag-service/            FastAPI + LangChain
    ├── main.py             /upload, /ask, /document/{id}
    ├── config.py
    └── rag/
        ├── loader.py       PDF / DOCX / TXT loaders
        ├── chunker.py      RecursiveCharacterTextSplitter
        ├── vectorstore.py  Gemini embeddings + ChromaDB
        └── qa.py           retrieval, relevance filter, grounded prompt
```

## Notes
- Scanned (image-only) PDFs have no text layer and need OCR first.
- If a model name errors out, change `CHAT_MODEL` / `EMBEDDING_MODEL` in `rag-service/.env` to one currently available for your key.
- Ideas to extend: chat history, multi-document search, streaming answers, user login, deployment (Render + Vercel).
