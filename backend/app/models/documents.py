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


@dataclass(frozen=True, slots=True)
class StagedUpload:
    """A safely persisted source file awaiting asynchronous processing."""

    document_id: str
    original_filename: str
    path: Path
    source_type: SourceType
    content_type: str | None
    size_bytes: int
