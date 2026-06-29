"""
API endpoints for CV tailoring.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response, Request
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator
import json
import logging
from pydantic import BaseModel, Field, ValidationError

from ..config import get_settings
from ..models.options import (
    TailorRequest,
    TailorOptions,
    ExtractJobRequest,
    ExtractCVRequest,
)
from ..models.output import (
    TailorResult,
    TailoredCV,
    CoverLetter,
    ChangeLogEntry,
    BorderlineItem,
    MatchScore,
)
from ..models.job_requirements import JobRequirements
from ..models.cv_facts import CVFacts
from ..models.mapping import MappingResult

from ..services.job_extractor import extract_job_requirements
from ..services.cv_extractor import extract_cv_facts
from ..services.mapper import map_requirements_to_evidence
from ..services.cv_generator import generate_tailored_cv
from ..services.cover_letter import generate_cover_letter
from ..services.qa_guardrails import run_quality_checks
from ..services.tailoring_pipeline import run_tailoring_pipeline, TailoringError

from ..utils.document_parser import extract_text, clean_extracted_text
from ..utils.exporters import generate_markdown, generate_docx, generate_pdf
from ..utils.prompt_security import (
    PromptInjectionError,
    scan_for_prompt_injection,
    validate_prompt_input,
)
from ..utils.rate_limit import limiter

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()
GENERIC_PROCESSING_MESSAGE = "The server failed to process the request. Please try again."


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


def _raise_server_error(error: str = "PROCESSING_ERROR") -> None:
    """Raise a generic 500 while preserving details in server logs only."""
    raise HTTPException(
        status_code=500,
        detail={"error": error, "message": GENERIC_PROCESSING_MESSAGE},
    )


def _raise_prompt_injection_error(exc: PromptInjectionError) -> None:
    """Return a consistent prompt-injection validation response."""
    raise HTTPException(
        status_code=400,
        detail={"error": "PROMPT_INJECTION_DETECTED", "message": str(exc)},
    )


def _validate_prompt_text(field_name: str, value: str | None) -> None:
    """Reject prompt-injection patterns in untrusted text."""
    try:
        validate_prompt_input(field_name, value)
    except PromptInjectionError as exc:
        _raise_prompt_injection_error(exc)


def _validate_prompt_model(value: BaseModel) -> None:
    """Reject prompt-injection patterns in structured step payloads."""
    try:
        scan_for_prompt_injection(value)
    except PromptInjectionError as exc:
        _raise_prompt_injection_error(exc)


async def _read_upload_file(cv_file: UploadFile) -> bytes:
    """Read a bounded upload body and reject files over the configured limit."""
    content = await cv_file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "UPLOAD_TOO_LARGE",
                "message": "Uploaded file is too large.",
            },
        )
    return content


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


def _build_mapping_summary(mapping: MappingResult) -> dict:
    """Build the mapping summary attached to a tailor result."""
    return {
        "overall_score": mapping.overall_match.score,
        "must_have_coverage": mapping.overall_match.must_have_coverage,
        "nice_to_have_coverage": mapping.overall_match.nice_to_have_coverage,
        "strongest_matches": mapping.overall_match.strongest_matches,
        "critical_gaps": mapping.overall_match.critical_gaps,
        "keywords_present": mapping.keyword_coverage.present_in_cv,
        "keywords_missing": mapping.keyword_coverage.genuinely_missing,
    }


# ---------------------------------------------------------------------------
# Step request/response models
#
# These power the client-orchestrated flow: the frontend calls one endpoint per
# pipeline stage so no single request approaches the serverless time limit.
# ---------------------------------------------------------------------------

class MapStepRequest(BaseModel):
    requirements: JobRequirements
    cv_facts: CVFacts
    strictness_level: str = "moderate"


class GenerateCVStepRequest(BaseModel):
    requirements: JobRequirements
    cv_facts: CVFacts
    mapping: MappingResult
    strictness_level: str = "moderate"
    user_instructions: Optional[str] = None


class GenerateCVStepResponse(BaseModel):
    tailored_cv: TailoredCV
    changes_log: list[ChangeLogEntry]
    borderline_items: list[BorderlineItem]
    match_score: MatchScore
    mapping_summary: dict
    warnings: list[str] = Field(default_factory=list)


class CoverLetterStepRequest(BaseModel):
    requirements: JobRequirements
    cv_facts: CVFacts
    mapping: MappingResult
    strictness_level: str = "moderate"
    user_instructions: Optional[str] = None


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
        _raise_server_error()


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
            yield _sse({"error": True, "message": GENERIC_PROCESSING_MESSAGE})

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
    _validate_prompt_text("job_description", job_description)
    _validate_prompt_text("user_instructions", user_instructions)

    async def generate_events() -> AsyncGenerator[str, None]:
        try:
            # Read file
            yield _sse({"step": 0, "total": 7, "message": "Reading uploaded CV file..."})
            content = await _read_upload_file(cv_file)
            cv_text = clean_extracted_text(extract_text(content, cv_file.filename or "upload.txt"))
            _validate_prompt_text("cv_text", cv_text)

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

        except HTTPException as e:
            detail = e.detail if isinstance(e.detail, dict) else {}
            yield _sse({
                "error": True,
                "code": detail.get("error", "UPLOAD_ERROR"),
                "message": detail.get("message", "Uploaded file could not be processed."),
            })
        except ValidationError as e:
            yield _sse({"error": True, "message": "Invalid options", "details": e.errors()})
        except TailoringError as e:
            yield _sse({"error": True, "message": e.message, "details": e.details})
        except Exception as e:
            logger.exception("Failed to tailor CV with file upload (streaming)")
            yield _sse({"error": True, "message": GENERIC_PROCESSING_MESSAGE})

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
    _validate_prompt_text("job_description", job_description)
    _validate_prompt_text("user_instructions", user_instructions)

    try:
        content = await _read_upload_file(cv_file)
        cv_text = clean_extracted_text(extract_text(content, cv_file.filename or "upload.txt"))
        _validate_prompt_text("cv_text", cv_text)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to parse uploaded CV")
        raise HTTPException(
            status_code=400,
            detail={"error": "PARSE_FAILURE", "message": "Could not extract text from file."},
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


# ---------------------------------------------------------------------------
# Client-orchestrated step endpoints
#
# The frontend drives the pipeline one stage at a time so each HTTP request
# stays well under the serverless time limit. /extract-job and /extract-cv
# (below) are the first two stages; these cover mapping, generation and the
# cover letter.
# ---------------------------------------------------------------------------

@router.post("/parse-file")
@limiter.limit("20/minute")
async def parse_file(request: Request, cv_file: UploadFile = File(...)):
    """Parse an uploaded CV file to plain text (stage 0 for file uploads)."""
    _validate_file(cv_file.filename)
    try:
        content = await _read_upload_file(cv_file)
        cv_text = clean_extracted_text(extract_text(content, cv_file.filename or "upload.txt"))
        _validate_prompt_text("cv_text", cv_text)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to parse uploaded CV")
        raise HTTPException(
            status_code=400,
            detail={"error": "PARSE_FAILURE", "message": "Could not extract text from file."},
        )
    return {"cv_text": cv_text}


@router.post("/map", response_model=MappingResult)
@limiter.limit("20/minute")
async def map_step(request: Request, body: MapStepRequest):
    """Map job requirements to CV evidence (stage 3)."""
    _validate_prompt_model(body)
    try:
        return await map_requirements_to_evidence(
            body.requirements, body.cv_facts, body.strictness_level
        )
    except Exception as e:
        logger.exception("Failed to map requirements to evidence")
        _raise_server_error()


@router.post("/generate-cv", response_model=GenerateCVStepResponse)
@limiter.limit("10/minute")
async def generate_cv_step(request: Request, body: GenerateCVStepRequest):
    """Generate the tailored CV and run quality checks (stages 4+5)."""
    _validate_prompt_model(body)
    try:
        tailored_cv, changes_log, borderline_items = await generate_tailored_cv(
            body.requirements,
            body.cv_facts,
            body.mapping,
            body.strictness_level,
            body.user_instructions,
        )
    except Exception as e:
        logger.exception("Failed to generate tailored CV")
        _raise_server_error()

    is_valid, errors, warnings, match_score = run_quality_checks(
        body.cv_facts,
        tailored_cv,
        body.mapping,
        changes_log,
        borderline_items,
    )

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "FABRICATION_DETECTED",
                "message": "Quality checks detected potential fabrication",
                "details": errors,
            },
        )

    return GenerateCVStepResponse(
        tailored_cv=tailored_cv,
        changes_log=changes_log,
        borderline_items=borderline_items,
        match_score=match_score,
        mapping_summary=_build_mapping_summary(body.mapping),
        warnings=warnings,
    )


@router.post("/cover-letter", response_model=CoverLetter)
@limiter.limit("10/minute")
async def cover_letter_step(request: Request, body: CoverLetterStepRequest):
    """Generate a cover letter (stage 6)."""
    _validate_prompt_model(body)
    try:
        return await generate_cover_letter(
            body.requirements,
            body.cv_facts,
            body.mapping,
            body.strictness_level,
            body.user_instructions,
        )
    except Exception as e:
        logger.exception("Failed to generate cover letter")
        _raise_server_error()


@router.post("/extract-job", response_model=JobRequirements)
@limiter.limit("20/minute")
async def extract_job(request: Request, extract_request: ExtractJobRequest):
    """Standalone job-requirements extraction for previewing."""
    try:
        return await extract_job_requirements(extract_request.job_description)
    except Exception as e:
        logger.exception("Failed to extract job requirements")
        _raise_server_error("EXTRACTION_FAILED")


@router.post("/extract-cv", response_model=CVFacts)
@limiter.limit("20/minute")
async def extract_cv(request: Request, extract_request: ExtractCVRequest):
    """Standalone CV-facts extraction for previewing."""
    try:
        return await extract_cv_facts(extract_request.cv_text)
    except Exception as e:
        logger.exception("Failed to extract CV facts")
        _raise_server_error("EXTRACTION_FAILED")


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
        _raise_server_error("EXPORT_FAILED")
