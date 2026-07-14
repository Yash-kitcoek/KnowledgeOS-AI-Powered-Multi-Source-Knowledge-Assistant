"""Request and response schemas for the HTTP API."""

from pydantic import BaseModel, Field

from backend.app.models.documents import SourceType


class UploadAcceptedResponse(BaseModel):
    """Response returned after a source file is safely staged."""

    document_id: str = Field(
        description="Identifier used by subsequent indexing and retrieval APIs."
    )
    filename: str
    source_type: SourceType
    size_bytes: int
    status: str = "staged"
