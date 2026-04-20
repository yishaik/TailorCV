"""
Module 2: CV Facts Extractor

Extracts ONLY verifiable facts from the original CV.
Uses parallel extraction for faster processing.
"""
import asyncio
import logging
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from ..models.cv_facts import (
    CVFacts, PersonalInfo, ProfessionalSummary,
    Experience, ResponsibilityFact, ExtractedFacts,
    Achievement, AchievementMetrics, Skills, InferredSkill,
    Education, Certification, Project, Language,
)
from ..utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sub-models for parallel extraction
# ---------------------------------------------------------------------------

class _PersonalAndSummary(BaseModel):
    """Personal info + professional summary extracted together."""
    personal_info: PersonalInfo
    professional_summary: Optional[ProfessionalSummary] = None


class _ExperienceList(BaseModel):
    """List of experiences for parallel extraction."""
    experience: list[Experience] = Field(default_factory=list)


class _SkillsAndEducation(BaseModel):
    """Skills, education, certifications, projects, languages."""
    skills: Skills = Field(default_factory=Skills)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompts (shorter = faster)
# ---------------------------------------------------------------------------

_PERSONAL_PROMPT = """Extract personal info and professional summary from this CV. Preserve exact wording.

CV:
{cv_text}"""

_EXPERIENCE_PROMPT = """Extract ALL work experience entries from this CV. For each:
- company, title, start_date (YYYY-MM), end_date (YYYY-MM or 'present')
- responsibilities: original_text + extracted_facts (action, technologies, context, result)
- achievements: original_text + metrics if quantified
Preserve exact wording. Generate unique UUIDs for each experience id.

CV:
{cv_text}"""

_SKILLS_PROMPT = """Extract skills, education, certifications, projects, and languages from this CV.
- explicitly_listed: skills literally written in the CV
- inferred_from_experience: skills clearly demonstrated (with evidence_source = experience id)
- education: institution, degree, field, graduation_year
Preserve exact wording.

CV:
{cv_text}"""


# ---------------------------------------------------------------------------
# Main extraction function (parallel)
# ---------------------------------------------------------------------------

async def extract_cv_facts(cv_text: str) -> CVFacts:
    """
    Extract verifiable facts from a CV using 3 parallel Gemini calls.

    Args:
        cv_text: Raw CV text (from file or input)

    Returns:
        Parsed CVFacts object with all verifiable information
    """
    client = get_llm_client()

    try:
        # Run 3 extractions in PARALLEL
        personal_result, experience_result, skills_result = await asyncio.gather(
            client.generate_structured(
                prompt=_PERSONAL_PROMPT.format(cv_text=cv_text),
                response_model=_PersonalAndSummary,
            ),
            client.generate_structured(
                prompt=_EXPERIENCE_PROMPT.format(cv_text=cv_text),
                response_model=_ExperienceList,
            ),
            client.generate_structured(
                prompt=_SKILLS_PROMPT.format(cv_text=cv_text),
                response_model=_SkillsAndEducation,
            ),
        )

        # Post-process: calculate durations if missing
        for exp in experience_result.experience:
            if exp.duration_months is None:
                exp.duration_months = _calculate_duration(exp.start_date, exp.end_date)

        # Validate inferred skills have valid evidence sources
        valid_exp_ids = {exp.id for exp in experience_result.experience}
        skills_result.skills.inferred_from_experience = [
            skill for skill in skills_result.skills.inferred_from_experience
            if skill.evidence_source in valid_exp_ids
        ]

        # Merge results
        result = CVFacts(
            personal_info=personal_result.personal_info,
            professional_summary=personal_result.professional_summary,
            experience=experience_result.experience,
            skills=skills_result.skills,
            education=skills_result.education,
            certifications=skills_result.certifications,
            projects=skills_result.projects,
            languages=skills_result.languages,
        )

        logger.info(f"Extracted CV facts for '{result.personal_info.name}'")
        return result

    except Exception as e:
        logger.error(f"Failed to extract CV facts: {e}")
        raise


def _calculate_duration(start_date: str, end_date: str) -> int:
    """
    Calculate duration in months between two dates.

    Args:
        start_date: Start date in YYYY-MM format
        end_date: End date in YYYY-MM format or 'present'

    Returns:
        Duration in months
    """
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
