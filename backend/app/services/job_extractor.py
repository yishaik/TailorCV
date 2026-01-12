"""
Module 1: Job Requirements Extractor

Parses job descriptions and extracts structured requirements.
"""
from ..models.job_requirements import (
    JobRequirements,
    Requirement,
    RequirementCategory,
    Responsibility,
    ATSKeywords,
    CultureSignals
)
from ..utils.llm_client import get_llm_client
import logging

logger = logging.getLogger(__name__)


JOB_EXTRACTION_PROMPT = """
Analyze the following job description and extract structured requirements.

Be thorough in extracting:
1. MUST HAVE requirements: Look for "required", "must have", "X+ years", "essential", "minimum qualifications"
2. NICE TO HAVE requirements: Look for "preferred", "bonus", "ideally", "advantage", "plus"
3. INFERRED requirements: Standard requirements for this role type that are implied but not stated
4. RESPONSIBILITIES: Main job duties and the skills they imply
5. ATS KEYWORDS: Technical terms, tools, methodologies, certifications mentioned
6. CULTURE SIGNALS: Work environment, values, team dynamics indicators

For each requirement, classify the category as one of:
- technical_skill: Programming languages, frameworks, tools, methodologies
- soft_skill: Communication, leadership, teamwork, etc.
- experience: Years of experience, domain experience
- certification: Specific certifications required
- education: Degree requirements

Extract exact keywords as they appear for ATS optimization.

JOB DESCRIPTION:
{job_description}
"""


async def extract_job_requirements(job_description: str) -> JobRequirements:
    """
    Extract structured requirements from a job description.
    
    Args:
        job_description: Raw job description text
    
    Returns:
        Parsed JobRequirements object
    """
    client = get_llm_client()
    
    prompt = JOB_EXTRACTION_PROMPT.format(job_description=job_description)
    
    try:
        result = await client.generate_structured(
            prompt=prompt,
            response_model=JobRequirements
        )
        
        # Post-process: ensure keywords are deduplicated
        all_keywords = set()
        for req in result.must_have + result.nice_to_have:
            all_keywords.update(req.keywords)
        
        # Update ATS keywords if empty
        if not result.ats_keywords.high_priority:
            # Extract most frequent keywords from requirements
            result.ats_keywords.high_priority = list(all_keywords)[:10]
        
        logger.info(f"Extracted job requirements for '{result.job_title}'")
        return result
    
    except Exception as e:
        logger.error(f"Failed to extract job requirements: {e}")
        raise


def get_keyword_priority_map(requirements: JobRequirements) -> dict[str, str]:
    """
    Create a map of keywords to their priority level.
    
    Args:
        requirements: Parsed job requirements
    
    Returns:
        Dict mapping keyword to priority (high/medium/contextual)
    """
    priority_map = {}
    
    for keyword in requirements.ats_keywords.high_priority:
        priority_map[keyword.lower()] = "high"
    
    for keyword in requirements.ats_keywords.medium_priority:
        if keyword.lower() not in priority_map:
            priority_map[keyword.lower()] = "medium"
    
    for keyword in requirements.ats_keywords.contextual:
        if keyword.lower() not in priority_map:
            priority_map[keyword.lower()] = "contextual"
    
    return priority_map


def get_all_required_skills(requirements: JobRequirements) -> list[str]:
    """
    Get a flat list of all required skills from a job description.
    
    Args:
        requirements: Parsed job requirements
    
    Returns:
        List of skill names/keywords
    """
    skills = set()
    
    for req in requirements.must_have + requirements.nice_to_have:
        if req.category in [RequirementCategory.TECHNICAL_SKILL, RequirementCategory.SOFT_SKILL]:
            skills.update(req.keywords)
    
    for resp in requirements.responsibilities:
        skills.update(resp.implied_skills)
    
    return list(skills)
