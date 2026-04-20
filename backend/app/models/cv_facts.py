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
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None


class ExtractedFacts(BaseModel):
    """Facts extracted from a responsibility."""
    
    action: str = Field(..., description="What they did")
    context: Optional[str] = None
    result: Optional[str] = None
    technologies: list[str] = Field(default_factory=list)
    scope: Optional[str] = None


class ResponsibilityFact(BaseModel):
    """A responsibility with extracted facts."""
    
    original_text: str = Field(..., description="Original text from CV")
    extracted_facts: ExtractedFacts


class AchievementMetrics(BaseModel):
    """Quantified metrics from an achievement."""
    
    type: Literal["percentage", "number", "currency", "time", "other"]
    value: str
    context: str


class Achievement(BaseModel):
    """An achievement with optional metrics."""
    
    original_text: str
    quantified: bool = False
    metrics: Optional[AchievementMetrics] = None


class Experience(BaseModel):
    """A work experience entry."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company: str
    title: str
    start_date: str = Field(..., description="YYYY-MM")
    end_date: str = Field(..., description="YYYY-MM or 'present'")
    duration_months: Optional[int] = None
    location: Optional[str] = None
    responsibilities: list[ResponsibilityFact] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)


class InferredSkill(BaseModel):
    """A skill inferred from experience."""
    
    skill: str
    evidence_source: str = Field(..., description="Experience ID")


class Skills(BaseModel):
    """Skills section of CV."""
    
    explicitly_listed: list[str] = Field(default_factory=list)
    inferred_from_experience: list[InferredSkill] = Field(default_factory=list)


class Education(BaseModel):
    """An education entry."""
    
    institution: str
    degree: str
    field: str
    graduation_year: Optional[int] = None
    achievements: list[str] = Field(default_factory=list)


class Certification(BaseModel):
    """A certification entry."""
    
    name: str
    issuer: str
    date: Optional[str] = None
    status: Literal["completed", "in_progress", "expired"] = "completed"


class Project(BaseModel):
    """A project entry."""
    
    name: str
    description: str
    technologies: list[str] = Field(default_factory=list)
    role: Optional[str] = None
    outcomes: list[str] = Field(default_factory=list)


class Language(BaseModel):
    """A language proficiency."""
    
    language: str
    proficiency: Optional[str] = None


class ProfessionalSummary(BaseModel):
    """Professional summary section."""
    
    original_text: Optional[str] = None
    extracted_claims: list[str] = Field(default_factory=list)


class CVFacts(BaseModel):
    """Complete extracted CV facts."""
    
    personal_info: PersonalInfo
    professional_summary: Optional[ProfessionalSummary] = None
    experience: list[Experience] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
