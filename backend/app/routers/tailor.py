"""
API endpoints for CV tailoring.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import json
import logging

from ..models.options import TailorRequest, TailorOptions
from ..models.output import TailorResult
from ..models.job_requirements import JobRequirements
from ..models.cv_facts import CVFacts

from ..services.job_extractor import extract_job_requirements
from ..services.cv_extractor import extract_cv_facts
from ..services.mapper import map_requirements_to_evidence
from ..services.cv_generator import generate_tailored_cv
from ..services.qa_guardrails import run_quality_checks
from ..services.cover_letter import generate_cover_letter

from ..utils.document_parser import extract_text, clean_extracted_text
from ..utils.exporters import generate_markdown, generate_docx, generate_pdf
from ..utils.llm_client import set_llm_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tailor", response_model=TailorResult)
async def tailor_cv(request: TailorRequest):
    """
    Main endpoint: Tailor a CV for a specific job description.
    
    This endpoint:
    1. Extracts requirements from the job description
    2. Extracts facts from the original CV
    3. Maps requirements to evidence
    4. Generates a tailored CV
    5. Runs quality checks
    6. Optionally generates a cover letter
    
    Returns the complete tailored result including CV, cover letter,
    changes log, and analysis.
    """
    try:
        # Step 1: Extract job requirements
        logger.info("Extracting job requirements...")
        requirements = await extract_job_requirements(request.job_description)
        
        # Step 2: Extract CV facts
        logger.info("Extracting CV facts...")
        cv_facts = await extract_cv_facts(request.original_cv)
        
        # Step 3: Map requirements to evidence
        logger.info("Mapping requirements to evidence...")
        mapping = await map_requirements_to_evidence(
            requirements,
            cv_facts,
            request.options.strictness_level
        )
        
        # Step 4: Generate tailored CV
        logger.info("Generating tailored CV...")
        tailored_cv, changes_log, borderline_items = await generate_tailored_cv(
            requirements,
            cv_facts,
            mapping,
            request.options.strictness_level,
            request.options.user_instructions
        )
        
        # Step 5: Run quality checks
        logger.info("Running quality checks...")
        is_valid, errors, warnings, match_score = run_quality_checks(
            cv_facts,
            tailored_cv,
            mapping,
            changes_log,
            borderline_items
        )
        
        if not is_valid:
            logger.error(f"Quality check failed: {errors}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "FABRICATION_DETECTED",
                    "message": "Quality checks detected potential fabrication",
                    "details": errors
                }
            )
        
        # Step 6: Generate cover letter if requested
        cover_letter = None
        if request.options.generate_cover_letter:
            logger.info("Generating cover letter...")
            cover_letter = await generate_cover_letter(
                requirements,
                cv_facts,
                mapping,
                request.options.strictness_level,
                request.options.user_instructions
            )
        
        # Build mapping summary
        mapping_summary = {
            "overall_score": mapping.overall_match.score,
            "must_have_coverage": mapping.overall_match.must_have_coverage,
            "nice_to_have_coverage": mapping.overall_match.nice_to_have_coverage,
            "strongest_matches": mapping.overall_match.strongest_matches,
            "critical_gaps": mapping.overall_match.critical_gaps,
            "keywords_present": mapping.keyword_coverage.present_in_cv,
            "keywords_missing": mapping.keyword_coverage.genuinely_missing
        }
        
        return TailorResult(
            tailored_cv=tailored_cv,
            cover_letter=cover_letter,
            changes_log=changes_log,
            borderline_items=borderline_items,
            match_score=match_score,
            mapping_summary=mapping_summary
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to tailor CV")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROCESSING_ERROR",
                "message": str(e)
            }
        )


@router.post("/tailor/upload")
async def tailor_cv_with_upload(
    job_description: str = Form(...),
    cv_file: UploadFile = File(...),
    generate_cover_letter: bool = Form(True),
    strictness_level: str = Form("moderate"),
    output_format: str = Form("markdown"),
    user_instructions: Optional[str] = Form(None)
):
    """
    Tailor a CV with file upload support.
    
    Accepts PDF, DOCX, or TXT files for the CV.
    """
    # Validate file type
    allowed_extensions = [".pdf", ".docx", ".doc", ".txt", ".md"]
    filename = cv_file.filename or "upload.txt"
    
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_FILE_TYPE",
                "message": f"Supported formats: {', '.join(allowed_extensions)}"
            }
        )
    
    # Extract text from file
    try:
        content = await cv_file.read()
        cv_text = extract_text(content, filename)
        cv_text = clean_extracted_text(cv_text)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PARSE_FAILURE",
                "message": f"Could not extract text from file: {e}"
            }
        )
    
    # Create request and process
    request = TailorRequest(
        job_description=job_description,
        original_cv=cv_text,
        options=TailorOptions(
            generate_cover_letter=generate_cover_letter,
            strictness_level=strictness_level,
            output_format=output_format,
            user_instructions=user_instructions
        )
    )
    
    return await tailor_cv(request)


@router.post("/extract-job", response_model=JobRequirements)
async def extract_job(job_description: str):
    """
    Standalone endpoint to extract job requirements.
    
    Useful for previewing what requirements will be extracted
    before running the full tailoring process.
    """
    try:
        return await extract_job_requirements(job_description)
    except Exception as e:
        logger.exception("Failed to extract job requirements")
        raise HTTPException(
            status_code=500,
            detail={"error": "EXTRACTION_FAILED", "message": str(e)}
        )


@router.post("/extract-cv", response_model=CVFacts)
async def extract_cv(cv_text: str):
    """
    Standalone endpoint to extract CV facts.
    
    Useful for previewing what facts will be extracted
    from the CV before running the full tailoring process.
    """
    try:
        return await extract_cv_facts(cv_text)
    except Exception as e:
        logger.exception("Failed to extract CV facts")
        raise HTTPException(
            status_code=500,
            detail={"error": "EXTRACTION_FAILED", "message": str(e)}
        )


@router.post("/export/{format}")
async def export_result(
    format: str,
    result: TailorResult
):
    """
    Export a tailored result to the specified format.
    
    Supported formats: markdown, docx, pdf
    """
    if format not in ["markdown", "docx", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_FORMAT", "message": "Supported: markdown, docx, pdf"}
        )
    
    try:
        if format == "markdown":
            content = generate_markdown(result.tailored_cv, result.cover_letter)
            return Response(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": "attachment; filename=tailored_cv.md"}
            )
        
        elif format == "docx":
            content = generate_docx(result.tailored_cv, result.cover_letter)
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": "attachment; filename=tailored_cv.docx"}
            )
        
        elif format == "pdf":
            content = generate_pdf(result.tailored_cv, result.cover_letter)
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=tailored_cv.pdf"}
            )
    
    except Exception as e:
        logger.exception(f"Failed to export as {format}")
        raise HTTPException(
            status_code=500,
            detail={"error": "EXPORT_FAILED", "message": str(e)}
        )


@router.post("/set-api-key")
async def set_api_key(api_key: str):
    """
    Set the Gemini API key for the current session.
    
    Note: This is for development/testing. In production,
    use environment variables.
    """
    try:
        set_llm_api_key(api_key)
        return {"status": "success", "message": "API key configured"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_API_KEY", "message": str(e)}
        )
