"""Tests for local retrieval and citation preservation."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from backend.app.database.repository import KnowledgeRepository
from backend.app.models.documents import SourceType, StagedUpload
from backend.app.services.answering import AnsweringService


class AnsweringServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory()
        root = Path(self._temporary_directory.name)
        self.repository = KnowledgeRepository(root / "knowledgeos.db")
        self.repository.initialize()
        source = root / "notes.txt"
        source.write_text(
            "KnowledgeOS keeps document content on your local machine.", encoding="utf-8"
        )
        self.repository.create_document(
            StagedUpload("document-1", "notes.txt", source, SourceType.TEXT, "text/plain", 59)
        )
        self.repository.store_chunks("document-1", [(source.read_text(encoding="utf-8"), None)])
        self.settings = SimpleNamespace(
            retrieval_limit=6, ollama_base_url="http://127.0.0.1:1", ollama_chat_model="missing"
        )

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def test_returns_relevant_passage_and_citation_without_ollama(self) -> None:
        answer, session_id, citations, used_model = AnsweringService(
            self.repository,
            self.settings,  # type: ignore[arg-type]
        ).answer("Where does KnowledgeOS keep content?")

        self.assertIn("local machine", answer)
        self.assertTrue(session_id)
        self.assertFalse(used_model)
        self.assertEqual(citations[0].filename, "notes.txt")

    def test_returns_helpful_answer_when_no_source_matches(self) -> None:
        answer, _, citations, _ = AnsweringService(
            self.repository,
            self.settings,  # type: ignore[arg-type]
        ).answer("What is the capital of France?")

        self.assertIn("couldn't find", answer)
        self.assertEqual(citations, [])
