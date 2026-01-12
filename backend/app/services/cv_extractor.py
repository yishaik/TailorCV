"""
Module 2: CV Facts Extractor

Extracts ONLY verifiable facts from the original CV.
No interpretation, no embellishment.
"""
from ..models.cv_facts import (
    CVFacts,
    PersonalInfo,
    ProfessionalSummary,
    Experience,
    ResponsibilityFact,
    ExtractedFacts,
    Achievement,
    AchievementMetrics,
    Skills,
    InferredSkill,
    Education,
    Certification,
    Project,
    Language
)
from ..utils.llm_client import get_llm_client
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_date
import logging
import re

logger = logging.getLogger(__name__)


CV_EXTRACTION_PROMPT = """
You are a precise CV parser. Extract ONLY verifiable facts from this CV.
DO NOT interpret, embellish, or assume anything not explicitly stated.

CRITICAL RULES:
1. Preserve original wording exactly - store in original_text fields
2. If information is ambiguous, leave it as null/empty
3. DO NOT upgrade or enhance any claims
4. Calculate durations in months between dates
5. Mark skills as "inferred" only if clearly demonstrated in experience (with evidence link)
6. Normalize all dates to YYYY-MM format
7. If proficiency level isn't stated, don't assume "expert"

For each experience entry:
- Extract the exact action taken (what they did)
- Note context only if explicitly stated (team size, budget, etc.)
- Include results only if the CV states them
- List only technologies explicitly mentioned

CV TEXT:
{cv_text}
"""


async def extract_cv_facts(cv_text: str) -> CVFacts:
    """
    Extract verifiable facts from a CV.
    
    Args:
        cv_text: Raw CV text (from file or input)
    
    Returns:
        Parsed CVFacts object with all verifiable information
    """
    client = get_llm_client()
    
    prompt = CV_EXTRACTION_PROMPT.format(cv_text=cv_text)
    
    try:
        result = await client.generate_structured(
            prompt=prompt,
            response_model=CVFacts
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
    """
    Calculate duration in months between two dates.
    
    Args:
        start_date: Start date in YYYY-MM format
        end_date: End date in YYYY-MM format or 'present'
    
    Returns:
        Duration in months
    """
    try:
        start = parse_date(start_date + "-01")
        
        if end_date.lower() == "present":
            from datetime import datetime
            end = datetime.now()
        else:
            end = parse_date(end_date + "-01")
        
        delta = relativedelta(end, start)
        return delta.years * 12 + delta.months
    
    except Exception:
        return 0


def get_total_experience_years(cv_facts: CVFacts) -> float:
    """
    Calculate total years of experience from CV.
    
    Args:
        cv_facts: Parsed CV facts
    
    Returns:
        Total experience in years
    """
    total_months = sum(
        exp.duration_months or 0 
        for exp in cv_facts.experience
    )
    return round(total_months / 12, 1)


def get_all_skills(cv_facts: CVFacts) -> list[str]:
    """
    Get all skills (explicit and inferred) from CV.
    
    Args:
        cv_facts: Parsed CV facts
    
    Returns:
        List of all skill names
    """
    skills = set(cv_facts.skills.explicitly_listed)
    skills.update(s.skill for s in cv_facts.skills.inferred_from_experience)
    
    # Also extract from experience technologies
    for exp in cv_facts.experience:
        for resp in exp.responsibilities:
            skills.update(resp.extracted_facts.technologies)
    
    # And project technologies
    for proj in cv_facts.projects:
        skills.update(proj.technologies)
    
    return list(skills)


def get_skill_evidence(cv_facts: CVFacts, skill: str) -> list[dict]:
    """
    Find evidence for a specific skill in the CV.
    
    Args:
        cv_facts: Parsed CV facts
        skill: Skill to find evidence for
    
    Returns:
        List of evidence items with source and text
    """
    skill_lower = skill.lower()
    evidence = []
    
    # Check explicit skills
    if any(s.lower() == skill_lower for s in cv_facts.skills.explicitly_listed):
        evidence.append({
            "source_type": "skill",
            "text": f"Listed in skills section: {skill}"
        })
    
    # Check experience
    for exp in cv_facts.experience:
        for resp in exp.responsibilities:
            if skill_lower in resp.original_text.lower():
                evidence.append({
                    "source_type": "experience",
                    "source_id": exp.id,
                    "text": resp.original_text
                })
            elif skill_lower in [t.lower() for t in resp.extracted_facts.technologies]:
                evidence.append({
                    "source_type": "experience",
                    "source_id": exp.id,
                    "text": resp.original_text
                })
    
    # Check projects
    for proj in cv_facts.projects:
        if skill_lower in proj.description.lower():
            evidence.append({
                "source_type": "project",
                "text": f"{proj.name}: {proj.description}"
            })
        elif skill_lower in [t.lower() for t in proj.technologies]:
            evidence.append({
                "source_type": "project",
                "text": f"{proj.name} - uses {skill}"
            })
    
    # Check certifications
    for cert in cv_facts.certifications:
        if skill_lower in cert.name.lower():
            evidence.append({
                "source_type": "certification",
                "text": f"{cert.name} from {cert.issuer}"
            })
    
    return evidence
