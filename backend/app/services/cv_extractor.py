"""
Module 2: CV Facts Extractor

Extracts ONLY verifiable facts from the original CV.
No interpretation, no embellishment.
"""
from ..models.cv_facts import (
    CVFacts, PersonalInfo, ProfessionalSummary,
    Experience, ResponsibilityFact, ExtractedFacts,
    Achievement, AchievementMetrics, Skills, InferredSkill,
    Education, Certification, Project, Language,
)
from ..utils.llm_client import get_llm_client
import logging

logger = logging.getLogger(__name__)

CV_EXTRACTION_PROMPT = """Extract ALL verifiable facts from this CV as structured JSON.
Rules: Preserve exact wording. Use YYYY-MM dates. Mark inferred skills with evidence link.

CV:
{cv_text}"""


async def extract_cv_facts(cv_text: str) -> CVFacts:
    """Extract verifiable facts from a CV."""
    client = get_llm_client()

    prompt = CV_EXTRACTION_PROMPT.format(cv_text=cv_text)

    try:
        result = await client.generate_structured(
            prompt=prompt,
            response_model=CVFacts,
        )

        # Post-process: calculate durations if missing
        for exp in result.experience:
            if exp.duration_months is None:
                exp.duration_months = _calculate_duration(exp.start_date, exp.end_date)

        # Validate inferred skills have valid evidence sources
        valid_exp_ids = {exp.id for exp in result.experience}
        result.skills.inferred_from_experience = [
            skill for skill in result.skills.inferred_from_experience
            if skill.evidence_source in valid_exp_ids
        ]

        logger.info(f"Extracted CV facts for '{result.personal_info.name}'")
        return result

    except Exception as e:
        logger.error(f"Failed to extract CV facts: {e}")
        raise


def _calculate_duration(start_date: str, end_date: str) -> int:
    """Calculate duration in months between two dates."""
    from dateutil.relativedelta import relativedelta
    from dateutil.parser import parse as parse_date
    from datetime import datetime

    try:
        start = parse_date(f"{start_date}-01")
        if end_date.lower() == "present":
            end = datetime.now()
        else:
            end = parse_date(f"{end_date}-01")
        delta = relativedelta(end, start)
        return delta.years * 12 + delta.months
    except Exception:
        return 0
