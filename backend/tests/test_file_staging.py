"""Unit tests for the upload staging boundary."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from backend.app.models.documents import SourceType
from backend.app.services.file_staging import (
    FileStagingService,
    UnsupportedSourceTypeError,
    UploadTooLargeError,
)


class FileStagingServiceTests(unittest.TestCase):
    """Verify file staging does not trust user supplied source metadata."""

    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory()
        self.settings = SimpleNamespace(
            upload_directory=Path(self._temporary_directory.name) / "uploads",
            max_upload_size_bytes=10,
        )
        self.service = FileStagingService(self.settings)  # type: ignore[arg-type]

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def test_stages_supported_file_with_generated_path(self) -> None:
        staged = self.service.stage(
            filename="../lecture-notes.md", content=b"knowledge", content_type="text/markdown"
        )

        self.assertEqual(staged.original_filename, "lecture-notes.md")
        self.assertEqual(staged.source_type, SourceType.TEXT)
        self.assertEqual(staged.size_bytes, 9)
        self.assertEqual(staged.path.read_bytes(), b"knowledge")
        self.assertNotEqual(staged.path.name, staged.original_filename)

    def test_rejects_unsupported_source_type(self) -> None:
        with self.assertRaises(UnsupportedSourceTypeError):
            self.service.stage(filename="payload.exe", content=b"data", content_type=None)

    def test_rejects_file_larger_than_configured_limit(self) -> None:
        with self.assertRaises(UploadTooLargeError):
            self.service.stage(
                filename="notes.txt", content=b"01234567890", content_type="text/plain"
            )
