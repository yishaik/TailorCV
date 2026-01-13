"""
Module 6: Cover Letter Generator

Generates a compelling cover letter that complements the tailored CV.
"""
from typing import Optional
from ..models.job_requirements import JobRequirements
from ..models.cv_facts import CVFacts
from ..models.mapping import MappingResult
from ..models.output import CoverLetter
from ..models.options import StrictnessConfig, STRICTNESS_CONFIGS
from ..utils.llm_client import get_llm_client
from .cv_extractor import get_total_experience_years
import logging

logger = logging.getLogger(__name__)


COVER_LETTER_PROMPT = """
Write a compelling cover letter for this job application.

JOB DETAILS:
- Title: {job_title}
- Company: {company}
- Key Requirements: {requirements}
- Culture Signals: {culture}

CANDIDATE PROFILE:
- Name: {name}
- Current Title: {current_title}
- Years of Experience: {years}
- Top Relevant Skills: {skills}
- Key Achievements: {achievements}

MATCH ANALYSIS:
- Overall Match Score: {match_score}%
- Strongest Matches: {strongest}
- Gaps to Address: {gaps}

STRUCTURE:
Write exactly 4 paragraphs:

1. HOOK (2-3 sentences):
   - Specific reference to company/role
   - Your strongest qualification match
   - Genuine enthusiasm

2. VALUE PROPOSITION (3-4 sentences):
   - Top 2-3 achievements relevant to this job
   - Use concrete examples with metrics when available
   - Mirror the job description language

3. FIT NARRATIVE (2-3 sentences):
   - Why you want THIS company specifically
   - How your background uniquely positions you
   - Address the most critical gap honestly if applicable

4. CLOSING (2 sentences):
   - Call to action
   - Express availability for discussion

RULES:
1. Maximum 400 words total
2. Never repeat CV content verbatim - expand and contextualize
3. Be specific, not generic
4. Match the company's tone ({tone})
5. If there are gaps, position them honestly with a growth mindset
6. Every claim must be based on the provided facts
7. If user notes are provided, incorporate their guidance appropriately

CRITICAL ACCURACY RULES - DO NOT VIOLATE:
- Every achievement and claim must come from the provided candidate profile
- Do NOT invent accomplishments, metrics, or experiences
- Do NOT exaggerate years of experience or skill levels
- Only mention skills that are explicitly listed in the profile
- Do NOT claim familiarity with technologies not mentioned in the CV
- Be honest about gaps - do not pretend they don't exist
{user_notes_section}

OUTPUT FORMAT:
Return a JSON object:
{{
    "hook": "paragraph 1 text",
    "value_proposition": "paragraph 2 text",
    "fit_narrative": "paragraph 3 text",
    "closing": "paragraph 4 text"
}}
"""


async def generate_cover_letter(
    requirements: JobRequirements,
    cv_facts: CVFacts,
    mapping: MappingResult,
    strictness: str = "moderate",
    user_notes: Optional[str] = None
) -> CoverLetter:
    """
    Generate a tailored cover letter.

    Args:
        requirements: Parsed job requirements
        cv_facts: Parsed CV facts
        mapping: Requirement-to-evidence mapping
        strictness: Strictness level
        user_notes: Optional user notes to guide generation

    Returns:
        Generated cover letter
    """
    config = STRICTNESS_CONFIGS.get(strictness, STRICTNESS_CONFIGS["moderate"])
    client = get_llm_client()
    
    # Gather data for cover letter
    current_title = ""
    key_achievements = []
    
    if cv_facts.experience:
        current_title = cv_facts.experience[0].title
        
        for exp in cv_facts.experience[:2]:
            for ach in exp.achievements:
                if ach.quantified:
                    key_achievements.append(ach.original_text)
            if len(key_achievements) >= 3:
                break
    
    # Get relevant skills
    relevant_skills = mapping.keyword_coverage.present_in_cv[:5]
    
    # Determine tone from culture signals
    tone = "professional"
    if requirements.culture_signals.work_style:
        if any("startup" in w.lower() or "dynamic" in w.lower() for w in requirements.culture_signals.work_style):
            tone = "energetic and dynamic"
        elif any("formal" in w.lower() or "traditional" in w.lower() for w in requirements.culture_signals.work_style):
            tone = "formal and traditional"
    
    # Format requirements
    req_text = "; ".join([r.description for r in requirements.must_have[:5]])
    
    # Format culture
    culture_text = ", ".join(
        requirements.culture_signals.work_style + 
        requirements.culture_signals.values
    )[:100] or "Not specified"
    
    # Format gaps
    gaps_text = ""
    if mapping.overall_match.critical_gaps:
        gaps_text = "; ".join(mapping.overall_match.critical_gaps[:2])
    
    # Build user notes section if provided
    user_notes_section = ""
    if user_notes:
        user_notes_section = f"\nUSER NOTES/INSTRUCTIONS:\n{user_notes}"

    prompt = COVER_LETTER_PROMPT.format(
        job_title=requirements.job_title,
        company=requirements.company or "the company",
        requirements=req_text,
        culture=culture_text,
        name=cv_facts.personal_info.name,
        current_title=current_title,
        years=f"{get_total_experience_years(cv_facts):.1f}",
        skills=", ".join(relevant_skills) or "Various relevant skills",
        achievements="; ".join(key_achievements) if key_achievements else "Various accomplishments",
        match_score=mapping.overall_match.score,
        strongest=", ".join(mapping.overall_match.strongest_matches[:3]) if mapping.overall_match.strongest_matches else "Multiple areas",
        gaps=gaps_text or "No critical gaps",
        tone=tone,
        user_notes_section=user_notes_section
    )
    
    try:
        response = await client.generate_text(prompt)
        
        # Parse JSON response
        import json
        if "{" in response:
            start = response.index("{")
            end = response.rindex("}") + 1
            data = json.loads(response[start:end])
            
            return CoverLetter(
                hook=data.get("hook", ""),
                value_proposition=data.get("value_proposition", ""),
                fit_narrative=data.get("fit_narrative", ""),
                closing=data.get("closing", "")
            )
    
    except Exception as e:
        logger.error(f"Failed to generate cover letter: {e}")
        raise
    
    # Fallback to basic generation
    return await _generate_basic_cover_letter(
        requirements, cv_facts, mapping, user_notes
    )


async def _generate_basic_cover_letter(
    requirements: JobRequirements,
    cv_facts: CVFacts,
    mapping: MappingResult,
    user_notes: Optional[str] = None
) -> CoverLetter:
    """Generate a basic cover letter as fallback.

    Note: This is a template-based fallback when LLM generation fails.
    User notes have limited effect here since no LLM is used.
    """
    
    name = cv_facts.personal_info.name
    job_title = requirements.job_title
    company = requirements.company or "your organization"
    years = get_total_experience_years(cv_facts)
    
    current_title = ""
    if cv_facts.experience:
        current_title = cv_facts.experience[0].title
    
    hook = (
        f"I am writing to express my strong interest in the {job_title} position at {company}. "
        f"With {years:.0f} years of experience as a {current_title}, I am confident in my ability "
        f"to contribute meaningfully to your team."
    )
    
    # Build value proposition from achievements
    achievements = []
    for exp in cv_facts.experience[:2]:
        for ach in exp.achievements:
            if ach.quantified:
                achievements.append(ach.original_text)
    
    if achievements:
        value_proposition = (
            f"Throughout my career, I have demonstrated consistent results. "
            f"{achievements[0]} "
        )
        if len(achievements) > 1:
            value_proposition += f"Additionally, {achievements[1]} "
        value_proposition += (
            f"These experiences have prepared me well for the challenges of the {job_title} role."
        )
    else:
        skills = mapping.keyword_coverage.present_in_cv[:3]
        value_proposition = (
            f"My expertise in {', '.join(skills) if skills else 'relevant areas'} "
            f"aligns well with the requirements of this position. I have a proven track record "
            f"of delivering results and collaborating effectively with cross-functional teams."
        )
    
    fit_narrative = (
        f"I am particularly drawn to {company} because of the opportunity to work on "
        f"challenging problems in a dynamic environment. My background in {current_title} "
        f"roles has given me the skills to hit the ground running and make an immediate impact."
    )
    
    closing = (
        f"I would welcome the opportunity to discuss how my experience and skills can "
        f"contribute to your team's success. Thank you for considering my application."
    )
    
    return CoverLetter(
        hook=hook,
        value_proposition=value_proposition,
        fit_narrative=fit_narrative,
        closing=closing
    )
