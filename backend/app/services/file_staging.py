"""Safe local staging for uploaded source files."""

from __future__ import annotations

from pathlib import Path, PurePath
from uuid import uuid4

from backend.app.config.settings import Settings
from backend.app.models.documents import SourceType, StagedUpload


class UnsupportedSourceTypeError(ValueError):
    """Raised when an upload is not handled by any configured processor."""


class UploadTooLargeError(ValueError):
    """Raised before an oversized upload is persisted."""


class FileStagingService:
    """Persist uploads under generated names while preserving their metadata."""

    _EXTENSION_TYPES: dict[str, SourceType] = {
        ".avi": SourceType.VIDEO,
        ".m4a": SourceType.AUDIO,
        ".mkv": SourceType.VIDEO,
        ".mov": SourceType.VIDEO,
        ".mp3": SourceType.AUDIO,
        ".mp4": SourceType.VIDEO,
        ".pdf": SourceType.DOCUMENT,
        ".png": SourceType.IMAGE,
        ".jpg": SourceType.IMAGE,
        ".jpeg": SourceType.IMAGE,
        ".webp": SourceType.IMAGE,
        ".docx": SourceType.DOCUMENT,
        ".pptx": SourceType.DOCUMENT,
        ".txt": SourceType.TEXT,
        ".md": SourceType.TEXT,
        ".markdown": SourceType.TEXT,
        ".wav": SourceType.AUDIO,
    }

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def stage(
        self, *, filename: str, content: bytes, content_type: str | None
    ) -> StagedUpload:
        """Validate and atomically stage one uploaded file.

        The caller's path is never trusted: only a basename is retained as
        display metadata, while the disk filename is a generated UUID.
        """

        safe_filename = PurePath(filename).name
        extension = Path(safe_filename).suffix.lower()
        source_type = self._EXTENSION_TYPES.get(extension)
        if not safe_filename or safe_filename == "." or source_type is None:
            raise UnsupportedSourceTypeError(f"Unsupported file type: {filename!r}")
        if len(content) > self._settings.max_upload_size_bytes:
            raise UploadTooLargeError(
                f"Upload exceeds {self._settings.max_upload_size_bytes} byte limit"
            )

        document_id = str(uuid4())
        destination = self._settings.upload_directory / f"{document_id}{extension}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = destination.with_suffix(f"{extension}.part")
        temporary_path.write_bytes(content)
        temporary_path.replace(destination)

        return StagedUpload(
            document_id=document_id,
            original_filename=safe_filename,
            path=destination,
            source_type=source_type,
            content_type=content_type,
            size_bytes=len(content),
        )
