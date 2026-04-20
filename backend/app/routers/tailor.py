"""
API endpoints for CV tailoring.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response, Request
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator
import json
import logging
from pydantic import ValidationError

from ..config import get_settings
from ..models.options import (
    TailorRequest,
    TailorOptions,
    ExtractJobRequest,
    ExtractCVRequest,
    ApiKeyRequest,
)
from ..models.output import TailorResult
from ..models.job_requirements import JobRequirements
from ..models.cv_facts import CVFacts

from ..services.job_extractor import extract_job_requirements
from ..services.cv_extractor import extract_cv_facts
from ..services.tailoring_pipeline import run_tailoring_pipeline, TailoringError

from ..utils.document_parser import extract_text, clean_extracted_text
from ..utils.exporters import generate_markdown, generate_docx, generate_pdf
from ..utils.llm_client import set_llm_api_key
from ..utils.rate_limit import limiter

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_file(filename: Optional[str]) -> None:
    """Raise HTTP 400 if the file extension is not allowed."""
    allowed = [".pdf", ".docx", ".txt", ".md"]
    name = filename or "upload.txt"
    if not any(name.lower().endswith(ext) for ext in allowed):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_FILE_TYPE",
                "message": f"Supported formats: {', '.join(allowed)}",
            },
        )


def _sse(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def _sse_headers() -> dict:
    """Standard SSE response headers."""
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/tailor", response_model=TailorResult)
@limiter.limit("10/minute")
async def tailor_cv(request: Request, tailor_request: TailorRequest):
    """
    Main endpoint: Tailor a CV for a specific job description.

    Runs the full pipeline and returns the result synchronously.
    """
    try:
        return await run_tailoring_pipeline(tailor_request)
    except TailoringError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": e.error_type, "message": e.message, "details": e.details},
        )
    except Exception as e:
        logger.exception("Failed to tailor CV")
        raise HTTPException(
            status_code=500,
            detail={"error": "PROCESSING_ERROR", "message": str(e)},
        )


@router.post("/tailor/stream")
@limiter.limit("10/minute")
async def tailor_cv_stream(request: Request, tailor_request: TailorRequest):
    """
    Streaming endpoint — SSE progress updates while tailoring.
    """
    async def generate_events() -> AsyncGenerator[str, None]:
        try:
            events: list[str] = []

            def on_step(step: int, total: int, message: str) -> None:
                events.append(_sse({"step": step, "total": total, "message": message}))

            result = await run_tailoring_pipeline(tailor_request, on_step=on_step)

            # Yield collected progress events, then final result
            for evt in events:
                yield evt
            yield _sse({"complete": True, "result": result.model_dump()})

        except TailoringError as e:
            yield _sse({"error": True, "message": e.message, "details": e.details})
        except Exception as e:
            logger.exception("Failed to tailor CV (streaming)")
            yield _sse({"error": True, "message": str(e)})

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


@router.post("/tailor/upload/stream")
@limiter.limit("10/minute")
async def tailor_cv_with_upload_stream(
    request: Request,
    job_description: str = Form(...),
    cv_file: UploadFile = File(...),
    generate_cover_letter: bool = Form(True),
    strictness_level: str = Form("moderate"),
    output_format: str = Form("markdown"),
    user_instructions: Optional[str] = Form(None),
):
    """
    Streaming file-upload endpoint — reads file then runs pipeline with SSE.
    """
    _validate_file(cv_file.filename)

    async def generate_events() -> AsyncGenerator[str, None]:
        try:
            # Read file
            yield _sse({"step": 0, "total": 7, "message": "Reading uploaded CV file..."})
            content = await cv_file.read()
            cv_text = clean_extracted_text(extract_text(content, cv_file.filename or "upload.txt"))

            options = TailorOptions(
                generate_cover_letter=generate_cover_letter,
                strictness_level=strictness_level,
                output_format=output_format,
                user_instructions=user_instructions,
            )
            tailor_req = TailorRequest(
                job_description=job_description,
                original_cv=cv_text,
                options=options,
            )

            events: list[str] = []

            def on_step(step: int, total: int, message: str) -> None:
                # Offset by 1 because step 0 was file reading
                events.append(_sse({"step": step + 1, "total": total + 1, "message": message}))

            result = await run_tailoring_pipeline(tailor_req, on_step=on_step)

            for evt in events:
                yield evt
            yield _sse({"complete": True, "result": result.model_dump()})

        except ValidationError as e:
            yield _sse({"error": True, "message": "Invalid options", "details": e.errors()})
        except TailoringError as e:
            yield _sse({"error": True, "message": e.message, "details": e.details})
        except Exception as e:
            logger.exception("Failed to tailor CV with file upload (streaming)")
            yield _sse({"error": True, "message": str(e)})

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


@router.post("/tailor/upload")
@limiter.limit("10/minute")
async def tailor_cv_with_upload(
    request: Request,
    job_description: str = Form(...),
    cv_file: UploadFile = File(...),
    generate_cover_letter: bool = Form(True),
    strictness_level: str = Form("moderate"),
    output_format: str = Form("markdown"),
    user_instructions: Optional[str] = Form(None),
):
    """
    Non-streaming file-upload endpoint.
    """
    _validate_file(cv_file.filename)

    try:
        content = await cv_file.read()
        cv_text = clean_extracted_text(extract_text(content, cv_file.filename or "upload.txt"))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "PARSE_FAILURE", "message": f"Could not extract text from file: {e}"},
        )

    try:
        options = TailorOptions(
            generate_cover_letter=generate_cover_letter,
            strictness_level=strictness_level,
            output_format=output_format,
            user_instructions=user_instructions,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_OPTIONS", "message": e.errors()},
        )

    tailor_req = TailorRequest(
        job_description=job_description,
        original_cv=cv_text,
        options=options,
    )

    return await run_tailoring_pipeline(tailor_req)


@router.post("/extract-job", response_model=JobRequirements)
@limiter.limit("20/minute")
async def extract_job(request: Request, extract_request: ExtractJobRequest):
    """Standalone job-requirements extraction for previewing."""
    try:
        return await extract_job_requirements(extract_request.job_description)
    except Exception as e:
        logger.exception("Failed to extract job requirements")
        raise HTTPException(
            status_code=500,
            detail={"error": "EXTRACTION_FAILED", "message": str(e)},
        )


@router.post("/extract-cv", response_model=CVFacts)
@limiter.limit("20/minute")
async def extract_cv(request: Request, extract_request: ExtractCVRequest):
    """Standalone CV-facts extraction for previewing."""
    try:
        return await extract_cv_facts(extract_request.cv_text)
    except Exception as e:
        logger.exception("Failed to extract CV facts")
        raise HTTPException(
            status_code=500,
            detail={"error": "EXTRACTION_FAILED", "message": str(e)},
        )


@router.post("/export/{format}")
@limiter.limit("30/minute")
async def export_result(
    request: Request,
    format: str,
    result: TailorResult,
):
    """Export a tailored result to markdown, docx, or pdf."""
    if format not in ("markdown", "docx", "pdf"):
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_FORMAT", "message": "Supported: markdown, docx, pdf"},
        )

    exporters = {
        "markdown": (generate_markdown, "text/markdown", "tailored_cv.md"),
        "docx": (generate_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "tailored_cv.docx"),
        "pdf": (generate_pdf, "application/pdf", "tailored_cv.pdf"),
    }

    try:
        gen_fn, media_type, filename = exporters[format]
        content = gen_fn(result.tailored_cv, result.cover_letter)
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.exception(f"Failed to export as {format}")
        raise HTTPException(
            status_code=500,
            detail={"error": "EXPORT_FAILED", "message": str(e)},
        )


@router.post("/set-api-key")
async def set_api_key(request: Request, api_key_request: ApiKeyRequest):
    """Set Gemini API key (debug mode only)."""
    try:
        if not settings.debug:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "FORBIDDEN",
                    "message": "API key updates are disabled outside debug mode",
                },
            )
        set_llm_api_key(api_key_request.api_key)
        return {"status": "success", "message": "API key configured"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_API_KEY", "message": str(e)},
        )
