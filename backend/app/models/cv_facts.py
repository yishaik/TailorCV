"""
Pydantic models for extracted CV facts.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import date
import uuid


class PersonalInfo(BaseModel):
    """Personal/contact information from CV."""
    
    name: str = Field(..., description="Full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="Location/city")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    website: Optional[str] = Field(default=None, description="Personal website/portfolio")


class ExtractedFacts(BaseModel):
    """Facts extracted from a responsibility."""
    
    action: str = Field(..., description="What they did")
    context: Optional[str] = Field(default=None, description="Where/how")
    result: Optional[str] = Field(default=None, description="Outcome if stated")
    technologies: list[str] = Field(default_factory=list, description="Technologies used")
    scope: Optional[str] = Field(default=None, description="Team size, budget, etc.")


class ResponsibilityFact(BaseModel):
    """A responsibility with extracted facts."""
    
    original_text: str = Field(..., description="Original text from CV")
    extracted_facts: ExtractedFacts = Field(..., description="Parsed facts")


class AchievementMetrics(BaseModel):
    """Quantified metrics from an achievement."""
    
    type: Literal["percentage", "number", "currency", "time", "other"] = Field(
        ..., description="Type of metric"
    )
    value: str = Field(..., description="The metric value")
    context: str = Field(..., description="Context for the metric")


class Achievement(BaseModel):
    """An achievement with optional metrics."""
    
    original_text: str = Field(..., description="Original text from CV")
    quantified: bool = Field(default=False, description="Whether the achievement is quantified")
    metrics: Optional[AchievementMetrics] = Field(default=None, description="Metrics if quantified")


class Experience(BaseModel):
    """A work experience entry."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    start_date: str = Field(..., description="Start date (YYYY-MM format)")
    end_date: str = Field(..., description="End date (YYYY-MM or 'present')")
    duration_months: Optional[int] = Field(default=None, description="Duration in months")
    location: Optional[str] = Field(default=None, description="Work location")
    
    responsibilities: list[ResponsibilityFact] = Field(
        default_factory=list,
        description="Responsibilities with extracted facts"
    )
    achievements: list[Achievement] = Field(
        default_factory=list,
        description="Achievements"
    )


class InferredSkill(BaseModel):
    """A skill inferred from experience."""
    
    skill: str = Field(..., description="The skill name")
    evidence_source: str = Field(..., description="Experience ID that evidences this skill")


class Skills(BaseModel):
    """Skills section of CV."""
    
    explicitly_listed: list[str] = Field(
        default_factory=list,
        description="Skills explicitly listed in CV"
    )
    inferred_from_experience: list[InferredSkill] = Field(
        default_factory=list,
        description="Skills inferred from experience sections"
    )


class Education(BaseModel):
    """An education entry."""
    
    institution: str = Field(..., description="School/university name")
    degree: str = Field(..., description="Degree type")
    field: str = Field(..., description="Field of study")
    graduation_year: Optional[int] = Field(default=None, description="Year of graduation")
    achievements: list[str] = Field(default_factory=list, description="Academic achievements")


class Certification(BaseModel):
    """A certification entry."""
    
    name: str = Field(..., description="Certification name")
    issuer: str = Field(..., description="Issuing organization")
    date: Optional[str] = Field(default=None, description="Date obtained")
    status: Literal["completed", "in_progress", "expired"] = Field(
        default="completed",
        description="Certification status"
    )


class Project(BaseModel):
    """A project entry."""
    
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    technologies: list[str] = Field(default_factory=list, description="Technologies used")
    role: Optional[str] = Field(default=None, description="Role in the project")
    outcomes: list[str] = Field(default_factory=list, description="Project outcomes")


class Language(BaseModel):
    """A language proficiency."""
    
    language: str = Field(..., description="Language name")
    proficiency: Optional[str] = Field(default=None, description="Proficiency level")


class ProfessionalSummary(BaseModel):
    """Professional summary section."""
    
    original_text: Optional[str] = Field(default=None, description="Original summary text")
    extracted_claims: list[str] = Field(
        default_factory=list,
        description="Factual claims from the summary"
    )


class CVFacts(BaseModel):
    """Complete extracted CV facts."""
    
    personal_info: PersonalInfo = Field(..., description="Personal information")
    professional_summary: Optional[ProfessionalSummary] = Field(
        default=None,
        description="Professional summary"
    )
    experience: list[Experience] = Field(
        default_factory=list,
        description="Work experience"
    )
    skills: Skills = Field(
        default_factory=Skills,
        description="Skills"
    )
    education: list[Education] = Field(
        default_factory=list,
        description="Education"
    )
    certifications: list[Certification] = Field(
        default_factory=list,
        description="Certifications"
    )
    projects: list[Project] = Field(
        default_factory=list,
        description="Projects"
    )
    languages: list[Language] = Field(
        default_factory=list,
        description="Languages"
    )
