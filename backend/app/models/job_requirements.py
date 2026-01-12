"""
Pydantic models for parsed job description data.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum


class RequirementCategory(str, Enum):
    """Categories for job requirements."""
    TECHNICAL_SKILL = "technical_skill"
    SOFT_SKILL = "soft_skill"
    EXPERIENCE = "experience"
    CERTIFICATION = "certification"
    EDUCATION = "education"


class Requirement(BaseModel):
    """A single job requirement."""
    
    category: RequirementCategory = Field(
        ...,
        description="Category of the requirement"
    )
    description: str = Field(
        ...,
        description="Full description of the requirement"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords associated with this requirement"
    )
    years_required: Optional[int] = Field(
        default=None,
        description="Years of experience required, if specified"
    )
    specificity: Literal["exact", "flexible"] = Field(
        default="flexible",
        description="Whether the requirement is exact or flexible"
    )


class Responsibility(BaseModel):
    """A job responsibility with implied skills."""
    
    description: str = Field(
        ...,
        description="Description of the responsibility"
    )
    implied_skills: list[str] = Field(
        default_factory=list,
        description="Skills implied by this responsibility"
    )


class ATSKeywords(BaseModel):
    """ATS keywords categorized by priority."""
    
    high_priority: list[str] = Field(
        default_factory=list,
        description="Keywords that appear multiple times or in requirements"
    )
    medium_priority: list[str] = Field(
        default_factory=list,
        description="Keywords that appear once in key sections"
    )
    contextual: list[str] = Field(
        default_factory=list,
        description="Industry/role standard terms"
    )


class CultureSignals(BaseModel):
    """Culture signals extracted from the job description."""
    
    work_style: list[str] = Field(
        default_factory=list,
        description="Work style indicators (e.g., 'fast-paced', 'collaborative')"
    )
    values: list[str] = Field(
        default_factory=list,
        description="Company values (e.g., 'innovation', 'customer-first')"
    )


class JobRequirements(BaseModel):
    """Complete parsed job requirements."""
    
    job_title: str = Field(
        ...,
        description="The job title"
    )
    company: Optional[str] = Field(
        default=None,
        description="Company name if mentioned"
    )
    department: Optional[str] = Field(
        default=None,
        description="Department if mentioned"
    )
    
    must_have: list[Requirement] = Field(
        default_factory=list,
        description="Required qualifications"
    )
    nice_to_have: list[Requirement] = Field(
        default_factory=list,
        description="Preferred qualifications"
    )
    inferred: list[Requirement] = Field(
        default_factory=list,
        description="Requirements implied but not explicitly stated"
    )
    
    responsibilities: list[Responsibility] = Field(
        default_factory=list,
        description="Job responsibilities"
    )
    
    ats_keywords: ATSKeywords = Field(
        default_factory=ATSKeywords,
        description="ATS-relevant keywords"
    )
    
    culture_signals: CultureSignals = Field(
        default_factory=CultureSignals,
        description="Culture and work environment signals"
    )
