"""
HTTP route: POST /api/analyze-image

Receives a JPEG/PNG photo from the phone and returns the parsed
step list. No file is persisted to disk.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.config import Settings, get_settings
from backend.dependencies import get_program_service
from backend.models import AnalyzeResponse
from backend.services.program_service import ProgramService

router = APIRouter(prefix="/api", tags=["vision"])


@router.post(
    "/analyze-image",
    response_model=AnalyzeResponse,
    summary="Analyze a photo of code blocks",
)
async def analyze_image(
    file: Annotated[UploadFile, File(description="JPEG or PNG of the code block layout")],
    service: Annotated[ProgramService, Depends(get_program_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnalyzeResponse:
    """
    Upload a photo → receive ordered step list for the cat to execute.
    """
    _validate_content_type(file.content_type)

    image_bytes = await file.read()
    _validate_size(len(image_bytes), settings.max_upload_bytes)

    result = service.analyze_image(image_bytes)
    return result


# ------------------------------------------------------------------
# Guards
# ------------------------------------------------------------------

def _validate_content_type(content_type: str | None) -> None:
    allowed = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    if content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{content_type}'. Upload JPEG or PNG.",
        )


def _validate_size(size: int, max_bytes: int) -> None:
    if size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({size} bytes). Max is {max_bytes} bytes.",
        )
