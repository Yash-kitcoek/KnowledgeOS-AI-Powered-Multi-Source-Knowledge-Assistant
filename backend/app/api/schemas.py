"""Request and response schemas for the HTTP API."""

from pydantic import BaseModel, Field

from backend.app.models.documents import DocumentStatus, SourceType


class UploadAcceptedResponse(BaseModel):
    """Response returned after a source file is safely staged."""

    document_id: str = Field(
        description="Identifier used by subsequent indexing and retrieval APIs."
    )
    filename: str
    source_type: SourceType
    size_bytes: int
    status: str = "staged"


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    source_type: SourceType
    size_bytes: int
    status: DocumentStatus
    error: str | None = None
    created_at: str


class CitationResponse(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    excerpt: str
    location: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2_000)
    session_id: str | None = Field(default=None, max_length=100)


class AskResponse(BaseModel):
    answer: str
    session_id: str
    citations: list[CitationResponse]
    used_local_model: bool
