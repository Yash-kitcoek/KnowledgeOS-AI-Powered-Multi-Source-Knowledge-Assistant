"""Endpoints that accept local knowledge sources."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.app.api.schemas import UploadAcceptedResponse
from backend.app.config.settings import Settings, get_settings
from backend.app.services.file_staging import (
    FileStagingService,
    UnsupportedSourceTypeError,
    UploadTooLargeError,
)

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.post("/upload", response_model=UploadAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...), settings: Settings = Depends(get_settings)
) -> UploadAcceptedResponse:
    """Stage an upload now; a worker will extract and index it in a later milestone."""

    content = await file.read()
    try:
        staged = FileStagingService(settings).stage(
            filename=file.filename or "", content=content, content_type=file.content_type
        )
    except UnsupportedSourceTypeError as error:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(error)) from error
    except UploadTooLargeError as error:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(error)) from error
    finally:
        await file.close()

    return UploadAcceptedResponse(
        document_id=staged.document_id,
        filename=staged.original_filename,
        source_type=staged.source_type,
        size_bytes=staged.size_bytes,
    )
