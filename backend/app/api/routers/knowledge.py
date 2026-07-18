"""Library, search, and RAG chat endpoints."""

from dataclasses import asdict
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.schemas import AskRequest, AskResponse, CitationResponse, DocumentResponse
from backend.app.config.settings import Settings, get_settings
from backend.app.database.repository import KnowledgeRepository
from backend.app.services.answering import AnsweringService

router = APIRouter(prefix="/v1", tags=["knowledge"])


def _repository(settings: Settings) -> KnowledgeRepository:
    return KnowledgeRepository(settings.database_path)


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(settings: Settings = Depends(get_settings)) -> list[DocumentResponse]:
    return [_document_response(row) for row in _repository(settings).documents()]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, settings: Settings = Depends(get_settings)) -> DocumentResponse:
    document = _repository(settings).document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _document_response(document)


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, settings: Settings = Depends(get_settings)) -> AskResponse:
    answer, session_id, citations, used_local_model = AnsweringService(
        _repository(settings), settings
    ).answer(request.question, request.session_id)
    return AskResponse(
        answer=answer, session_id=session_id, used_local_model=used_local_model,
        citations=[CitationResponse(**asdict(citation)) for citation in citations],
    )


def _document_response(row: sqlite3.Row) -> DocumentResponse:
    return DocumentResponse(
        document_id=row["id"], filename=row["filename"], source_type=row["source_type"],
        size_bytes=row["size_bytes"], status=row["status"], error=row["error"],
        created_at=row["created_at"],
    )
