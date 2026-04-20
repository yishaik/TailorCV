"""
Core CV tailoring pipeline.

Shared logic used by all tailor endpoints (streaming, non-streaming, upload).
"""
import logging
import time
from typing import Optional

from ..models.options import TailorRequest
from ..models.output import TailorResult

from .job_extractor import extract_job_requirements
from .cv_extractor import extract_cv_facts
from .mapper import map_requirements_to_evidence
from .cv_generator import generate_tailored_cv
from .qa_guardrails import run_quality_checks
from .cover_letter import generate_cover_letter

logger = logging.getLogger(__name__)


class TailoringError(Exception):
    """Raised when quality checks fail or tailoring cannot proceed."""

    def __init__(self, error_type: str, message: str, details: Optional[list] = None):
        self.error_type = error_type
        self.message = message
        self.details = details or []
        super().__init__(message)


async def run_tailoring_pipeline(
    request: TailorRequest,
    on_step: Optional[callable] = None,
) -> TailorResult:
    """
    Execute the full CV tailoring pipeline.

    Args:
        request: The tailoring request with job description, CV, and options.
        on_step: Optional callback(step_number, total_steps, message) for progress.

    Returns:
        TailorResult with tailored CV, cover letter, and analysis.

    Raises:
        TailoringError: If quality checks detect fabrication.
    """
    total_steps = 7 if request.options.generate_cover_letter else 6

    def _notify(step: int, message: str) -> None:
        if on_step:
            on_step(step, total_steps, message)

    # Step 1: Extract job requirements
    _notify(1, "Analyzing job description...")
    t0 = time.time()
    requirements = await extract_job_requirements(request.job_description)
    logger.info(f"Step 1 (extract_job) took {time.time()-t0:.1f}s")

    # Step 2: Extract CV facts
    _notify(2, "Extracting CV facts...")
    t0 = time.time()
    cv_facts = await extract_cv_facts(request.original_cv)
    logger.info(f"Step 2 (extract_cv) took {time.time()-t0:.1f}s")

    # Step 3: Map requirements to evidence
    _notify(3, "Mapping requirements to experience...")
    t0 = time.time()
    mapping = await map_requirements_to_evidence(
        requirements,
        cv_facts,
        request.options.strictness_level,
    )
    logger.info(f"Step 3 (mapper) took {time.time()-t0:.1f}s")

    # Step 4: Generate tailored CV
    _notify(4, "Generating tailored CV...")
    t0 = time.time()
    tailored_cv, changes_log, borderline_items = await generate_tailored_cv(
        requirements,
        cv_facts,
        mapping,
        request.options.strictness_level,
        request.options.user_instructions,
    )
    logger.info(f"Step 4 (generate_cv) took {time.time()-t0:.1f}s")

    # Step 5: Run quality checks
    _notify(5, "Running quality checks...")
    is_valid, errors, warnings, match_score = run_quality_checks(
        cv_facts,
        tailored_cv,
        mapping,
        changes_log,
        borderline_items,
    )

    if not is_valid:
        raise TailoringError(
            error_type="FABRICATION_DETECTED",
            message="Quality checks detected potential fabrication",
            details=errors,
        )

    # Step 6 (or 7): Generate cover letter or finalize
    cover_letter = None
    if request.options.generate_cover_letter:
        _notify(6, "Generating cover letter...")
        t0 = time.time()
        cover_letter = await generate_cover_letter(
            requirements,
            cv_facts,
            mapping,
            request.options.strictness_level,
            request.options.user_instructions,
        )
        logger.info(f"Step 6 (cover_letter) took {time.time()-t0:.1f}s")
    else:
        _notify(6, "Finalizing...")

    # Build mapping summary
    mapping_summary = {
        "overall_score": mapping.overall_match.score,
        "must_have_coverage": mapping.overall_match.must_have_coverage,
        "nice_to_have_coverage": mapping.overall_match.nice_to_have_coverage,
        "strongest_matches": mapping.overall_match.strongest_matches,
        "critical_gaps": mapping.overall_match.critical_gaps,
        "keywords_present": mapping.keyword_coverage.present_in_cv,
        "keywords_missing": mapping.keyword_coverage.genuinely_missing,
    }

    return TailorResult(
        tailored_cv=tailored_cv,
        cover_letter=cover_letter,
        changes_log=changes_log,
        borderline_items=borderline_items,
        match_score=match_score,
        mapping_summary=mapping_summary,
    )
