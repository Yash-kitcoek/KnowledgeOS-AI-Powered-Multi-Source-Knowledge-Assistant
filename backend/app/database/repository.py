"""Small SQLite repository that owns documents, chunks, and conversations."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

from backend.app.models.documents import DocumentStatus, SourceType, StagedUpload


class KnowledgeRepository:
    """Persist metadata separately from files and embeddings.

    SQLite is suitable for the single-node portfolio deployment. Keeping this
    interface narrow makes a later PostgreSQL migration an infrastructure swap.
    """

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    path TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    content_type TEXT,
                    size_bytes INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    location TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(document_id, chunk_index)
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
                CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
                """
            )

    def create_document(self, upload: StagedUpload) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO documents
                (id, filename, path, source_type, content_type, size_bytes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    upload.document_id,
                    upload.original_filename,
                    str(upload.path),
                    upload.source_type,
                    upload.content_type,
                    upload.size_bytes,
                    DocumentStatus.STAGED,
                ),
            )

    def document(self, document_id: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()

    def documents(self) -> list[sqlite3.Row]:
        """Return documents newest first for the library view."""

        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM documents ORDER BY created_at DESC, rowid DESC"
            ).fetchall()

    def store_chunks(self, document_id: str, chunks: list[tuple[str, str | None]]) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.executemany(
                "INSERT INTO chunks (id, document_id, chunk_index, text, location) VALUES (?, ?, ?, ?, ?)",
                [(str(uuid4()), document_id, index, text, location) for index, (text, location) in enumerate(chunks)],
            )
            connection.execute(
                "UPDATE documents SET status = ?, error = NULL WHERE id = ?",
                (DocumentStatus.INDEXED, document_id),
            )

    def mark_failed(self, document_id: str, error: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE documents SET status = ?, error = ? WHERE id = ?",
                (DocumentStatus.FAILED, error[:1000], document_id),
            )

    def search_chunks(self, query: str, limit: int) -> list[sqlite3.Row]:
        terms = [term for term in query.lower().split() if len(term) > 1]
        if not terms:
            return []
        where = " OR ".join("lower(chunks.text) LIKE ?" for _ in terms)
        parameters = [f"%{term}%" for term in terms]
        score = " + ".join("CASE WHEN lower(chunks.text) LIKE ? THEN 1 ELSE 0 END" for _ in terms)
        parameters.extend(f"%{term}%" for term in terms)
        parameters.append(limit)
        with self._connect() as connection:
            return connection.execute(
                f"""SELECT chunks.*, documents.filename, ({score}) AS relevance
                FROM chunks JOIN documents ON documents.id = chunks.document_id
                WHERE {where}
                ORDER BY relevance DESC, chunks.created_at DESC LIMIT ?""",
                parameters,
            ).fetchall()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                (str(uuid4()), session_id, role, content),
            )

    def history(self, session_id: str, limit: int = 10) -> list[sqlite3.Row]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT role, content FROM messages WHERE session_id = ?
                ORDER BY created_at DESC, rowid DESC LIMIT ?""",
                (session_id, limit),
            ).fetchall()
        return list(reversed(rows))

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection
