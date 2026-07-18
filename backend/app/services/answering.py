"""Retrieval-augmented answering with an optional local Ollama model."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from backend.app.config.settings import Settings
from backend.app.database.repository import KnowledgeRepository
from backend.app.models.documents import Citation


class AnsweringService:
    """Answer only from indexed local sources and always retain citations."""

    def __init__(self, repository: KnowledgeRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    def answer(self, question: str, session_id: str | None = None) -> tuple[str, str, list[Citation], bool]:
        session_id = session_id or str(uuid4())
        matches = self._repository.search_chunks(question, self._settings.retrieval_limit)
        citations = [
            Citation(
                document_id=row["document_id"], filename=row["filename"], chunk_id=row["id"],
                excerpt=row["text"][:320], location=row["location"],
            )
            for row in matches
        ]
        self._repository.add_message(session_id, "user", question)
        if not matches:
            answer = "I couldn't find this in your indexed documents. Upload relevant material and try again."
            self._repository.add_message(session_id, "assistant", answer)
            return answer, session_id, citations, False

        context = "\n\n".join(
            f"[{index + 1}] {row['filename']} ({row['location'] or 'document'}): {row['text']}"
            for index, row in enumerate(matches)
        )
        answer = self._ask_ollama(question, context)
        used_local_model = answer is not None
        if answer is None:
            answer = (
                "Here are the most relevant passages from your knowledge base:\n\n"
                + "\n\n".join(f"[{index + 1}] {row['text']}" for index, row in enumerate(matches))
            )
        self._repository.add_message(session_id, "assistant", answer)
        return answer, session_id, citations, used_local_model

    def _ask_ollama(self, question: str, context: str) -> str | None:
        payload = json.dumps({
            "model": self._settings.ollama_chat_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": "Answer only using the supplied context. Cite passages as [1], [2]. If context is insufficient, say so."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
        }).encode("utf-8")
        request = Request(
            f"{self._settings.ollama_base_url.rstrip('/')}/api/chat",
            data=payload, headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:  # nosec B310 - configured local URL
                text = json.loads(response.read().decode("utf-8"))["message"]["content"].strip()
                return text or None
        except (URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError):
            return None
