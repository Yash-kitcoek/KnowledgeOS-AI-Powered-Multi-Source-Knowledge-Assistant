"""Document-ingestion domain types."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class SourceType(StrEnum):
    """Supported upload categories before a processor extracts content."""

    AUDIO = "audio"
    DOCUMENT = "document"
    IMAGE = "image"
    TEXT = "text"
    VIDEO = "video"


class DocumentStatus(StrEnum):
    """Lifecycle state for a source document."""

    STAGED = "staged"
    INDEXED = "indexed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class StagedUpload:
    """A safely persisted source file awaiting asynchronous processing."""

    document_id: str
    original_filename: str
    path: Path
    source_type: SourceType
    content_type: str | None
    size_bytes: int


@dataclass(frozen=True, slots=True)
class Citation:
    """A stable reference to the local knowledge used in an answer."""

    document_id: str
    filename: str
    chunk_id: str
    excerpt: str
    location: str | None = None
