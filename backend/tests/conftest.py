"""
Shared test fixtures and factory functions.

Provides mock data factories for all major Pydantic models
so tests can build realistic objects without calling the LLM.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.models.cv_facts import (
    CVFacts, PersonalInfo, Experience, ResponsibilityFact,
    ExtractedFacts, Skills, InferredSkill, Achievement,
    AchievementMetrics, Education, Project,
)
from app.models.job_requirements import JobRequirements, Requirement
from app.models.mapping import (
    MappingResult, OverallMatch, KeywordCoverage,
    MappingEntry, RequirementRef, GapAnalysis, EvidenceItem,
)
from app.models.output import (
    TailoredCV, TailoredHeader, TailoredExperience,
    TailoredExperienceBullet, TailoredSkills, MatchScore,
    MatchScoreBreakdown, CoverLetter, ChangeLogEntry,
)
from app.models.options import TailorRequest, TailorOptions


# ---------------------------------------------------------------------------
# CV Facts factories
# ---------------------------------------------------------------------------

def make_cv_facts(**overrides) -> CVFacts:
    """Build a minimal valid CVFacts."""
    defaults = dict(
        personal_info=PersonalInfo(name="Jane Doe", email="jane@example.com"),
        experience=[
            Experience(
                company="Acme Corp",
                title="Software Engineer",
                start_date="2020-01",
                end_date="present",
                responsibilities=[
                    ResponsibilityFact(
                        original_text="Built REST APIs with Python and FastAPI",
                        extracted_facts=ExtractedFacts(
                            action="Built REST APIs",
                            technologies=["Python", "FastAPI"],
                        ),
                    ),
                ],
                achievements=[
                    Achievement(
                        original_text="Reduced latency by 30%",
                        quantified=True,
                        metrics=AchievementMetrics(type="percentage", value="30%", context="latency"),
                    ),
                ],
            ),
        ],
        skills=Skills(
            explicitly_listed=["Python", "FastAPI", "Docker"],
            inferred_from_experience=[
                InferredSkill(skill="REST APIs", evidence_source="exp-1"),
            ],
        ),
        education=[
            Education(institution="MIT", degree="BSc", field="Computer Science", graduation_year=2019),
        ],
    )
    defaults.update(overrides)
    return CVFacts(**defaults)


# ---------------------------------------------------------------------------
# Job Requirements factories
# ---------------------------------------------------------------------------

def make_job_requirements(**overrides) -> JobRequirements:
    defaults = dict(
        title="Senior Python Developer",
        company="TechCo",
        must_have=[
            Requirement(text="3+ years Python", category="experience", evidence_type="explicit"),
            Requirement(text="REST API development", category="skills", evidence_type="explicit"),
        ],
        nice_to_have=[
            Requirement(text="Docker experience", category="skills", evidence_type="explicit"),
        ],
    )
    defaults.update(overrides)
    return JobRequirements(**defaults)


# ---------------------------------------------------------------------------
# Mapping factories
# ---------------------------------------------------------------------------

def make_mapping(**overrides) -> MappingResult:
    defaults = dict(
        overall_match=OverallMatch(
            score=75,
            must_have_coverage="2/2",
            nice_to_have_coverage="1/1",
            strongest_matches=["Python", "REST APIs"],
            critical_gaps=[],
        ),
        keyword_coverage=KeywordCoverage(
            present_in_cv=["Python", "FastAPI", "REST"],
            missing_but_addressable=[],
            genuinely_missing=[],
        ),
    )
    defaults.update(overrides)
    return MappingResult(**defaults)


# ---------------------------------------------------------------------------
# Tailored CV factories
# ---------------------------------------------------------------------------

def make_tailored_cv(**overrides) -> TailoredCV:
    defaults = dict(
        header=TailoredHeader(
            name="Jane Doe",
            title="Senior Python Developer",
            contact={"email": "jane@example.com"},
        ),
        summary="Experienced Python engineer with 5 years building REST APIs.",
        experience=[
            TailoredExperience(
                company="Acme Corp",
                title="Software Engineer",
                dates="2020 - Present",
                bullets=[
                    TailoredExperienceBullet(
                        text="Built REST APIs with Python and FastAPI, reducing latency by 30%",
                        keywords_used=["Python", "FastAPI", "REST"],
                    ),
                ],
            ),
        ],
        skills=TailoredSkills(
            primary=["Python", "FastAPI", "REST APIs"],
            secondary=["Docker"],
            tools=["Git", "Docker"],
        ),
    )
    defaults.update(overrides)
    return TailoredCV(**defaults)


# ---------------------------------------------------------------------------
# Request factories
# ---------------------------------------------------------------------------

JOB_DESCRIPTION = (
    "We are looking for a Senior Python Developer with 3+ years of experience "
    "building REST APIs. Familiarity with Docker is a plus. You will design and "
    "implement scalable backend services for our growing platform."
)

CV_TEXT = (
    "Jane Doe\njane@example.com\n\n"
    "Software Engineer at Acme Corp (2020-Present)\n"
    "- Built REST APIs with Python and FastAPI\n"
    "- Reduced latency by 30%\n\n"
    "Skills: Python, FastAPI, Docker\n"
    "Education: BSc Computer Science, MIT, 2019"
)


def make_tailor_request(**overrides) -> TailorRequest:
    defaults = dict(
        job_description=JOB_DESCRIPTION,
        original_cv=CV_TEXT,
        options=TailorOptions(),
    )
    defaults.update(overrides)
    return TailorRequest(**defaults)


# ---------------------------------------------------------------------------
# Match score factory
# ---------------------------------------------------------------------------

def make_match_score(score: int = 75) -> MatchScore:
    return MatchScore(
        score=score,
        breakdown=MatchScoreBreakdown(
            must_have_component=50.0,
            nice_to_have_component=25.0,
            bonuses=["+3 for keyword integration"],
            penalties=[],
        ),
        explanation="Good match - candidate meets core requirements with some gaps",
    )
