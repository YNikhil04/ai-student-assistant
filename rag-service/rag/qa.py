"""Retrieval + grounded answer generation with Gemini."""
from typing import Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

import config
from rag import vectorstore

# Chunks scoring below this are treated as "not in the document".
MIN_RELEVANCE = 0.30

NOT_FOUND = "I couldn't find this in the uploaded document."

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a study assistant. Answer the student's question using ONLY "
            "the context excerpts from their document.\n"
            "Rules:\n"
            "1. If the answer is not clearly supported by the context, reply "
            f"exactly: \"{NOT_FOUND}\"\n"
            "2. Never use outside knowledge or guess.\n"
            "3. Be clear and concise; use short bullet points for lists or steps.\n"
            "4. Mention page numbers like (p. 3) when the context provides them.",
        ),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)

_chain = None


def _get_chain():
    global _chain
    if _chain is None:
        llm = ChatGoogleGenerativeAI(
            model=config.CHAT_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0.1,  # low temperature = fewer hallucinations
        )
        _chain = PROMPT | llm | StrOutputParser()
    return _chain


def _page_label(meta: Dict) -> str:
    page = meta.get("page")
    return f"p. {int(page) + 1}" if isinstance(page, (int, float)) else "n/a"


def answer_question(question: str, doc_id: str) -> Dict:
    results = vectorstore.search(question, doc_id, k=config.TOP_K)
    relevant = [(d, s) for d, s in results if s >= MIN_RELEVANCE]

    if not relevant:
        return {"answer": NOT_FOUND, "sources": []}

    context = "\n\n".join(
        f"[Excerpt {i + 1} | {_page_label(d.metadata)}]\n{d.page_content}"
        for i, (d, _) in enumerate(relevant)
    )

    answer = _get_chain().invoke({"context": context, "question": question})

    sources: List[Dict] = [
        {
            "page": _page_label(d.metadata),
            "score": round(float(s), 3),
            "snippet": d.page_content[:300].strip(),
        }
        for d, s in relevant
    ]
    return {"answer": answer.strip(), "sources": sources}
