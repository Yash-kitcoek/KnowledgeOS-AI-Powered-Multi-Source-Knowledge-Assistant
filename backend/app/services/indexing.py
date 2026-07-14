"""Document extraction, cleaning, and chunking orchestration."""

from __future__ import annotations

import re
from pathlib import Path

from backend.app.database.repository import KnowledgeRepository
from backend.app.processors.extractors import extract_text


class IndexingService:
    """Convert staged files into retrieval-ready text chunks."""

    def __init__(self, repository: KnowledgeRepository, chunk_size: int = 900) -> None:
        self._repository = repository
        self._chunk_size = chunk_size

    def index(self, document_id: str) -> None:
        document = self._repository.document(document_id)
        if document is None:
            raise LookupError(f"Document {document_id} does not exist")
        try:
            chunks = [
                (chunk, location)
                for text, location in extract_text(Path(document["path"]))
                for chunk in self._chunk(clean_text(text))
            ]
            if not chunks:
                raise ValueError("No extractable text was found in this source")
            self._repository.store_chunks(document_id, chunks)
        except Exception as error:
            self._repository.mark_failed(document_id, str(error))
            raise

    def _chunk(self, text: str) -> list[str]:
        if len(text) <= self._chunk_size:
            return [text] if text else []
        return [
            text[index : index + self._chunk_size]
            for index in range(0, len(text), self._chunk_size)
        ]


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving the source's language and meaning."""

    return re.sub(r"\s+", " ", text).strip()
