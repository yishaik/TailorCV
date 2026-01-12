"""
Pydantic models for tailored CV output.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional


class TailoredHeader(BaseModel):
    """Tailored header section."""
    
    name: str = Field(..., description="Full name")
    title: str = Field(..., description="Professional title aligned to job")
    contact: dict = Field(default_factory=dict, description="Contact information")


class TailoredExperienceBullet(BaseModel):
    """A single experience bullet point."""
    
    text: str = Field(..., description="The bullet text")
    keywords_used: list[str] = Field(
        default_factory=list,
        description="Keywords integrated in this bullet"
    )


class TailoredExperience(BaseModel):
    """A tailored experience entry."""
    
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    dates: str = Field(..., description="Date range")
    location: Optional[str] = Field(default=None, description="Location")
    bullets: list[TailoredExperienceBullet] = Field(
        default_factory=list,
        description="Experience bullets"
    )


class TailoredSkills(BaseModel):
    """Tailored skills section."""
    
    primary: list[str] = Field(
        default_factory=list,
        description="Primary skills (most relevant to job)"
    )
    secondary: list[str] = Field(
        default_factory=list,
        description="Secondary skills"
    )
    tools: list[str] = Field(
        default_factory=list,
        description="Tools and technologies"
    )


class TailoredEducation(BaseModel):
    """A tailored education entry."""
    
    institution: str = Field(..., description="School name")
    degree: str = Field(..., description="Degree")
    field: str = Field(..., description="Field of study")
    year: Optional[str] = Field(default=None, description="Graduation year")
    highlights: list[str] = Field(
        default_factory=list,
        description="Relevant highlights"
    )


class TailoredCertification(BaseModel):
    """A tailored certification entry."""
    
    name: str = Field(..., description="Certification name")
    issuer: str = Field(..., description="Issuer")
    date: Optional[str] = Field(default=None, description="Date")


class TailoredProject(BaseModel):
    """A tailored project entry."""
    
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Tailored description")
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies used"
    )


class TailoredCV(BaseModel):
    """Complete tailored CV."""
    
    header: TailoredHeader = Field(..., description="Header section")
    summary: str = Field(..., description="Professional summary")
    experience: list[TailoredExperience] = Field(
        default_factory=list,
        description="Experience section"
    )
    skills: TailoredSkills = Field(
        default_factory=TailoredSkills,
        description="Skills section"
    )
    education: list[TailoredEducation] = Field(
        default_factory=list,
        description="Education section"
    )
    certifications: list[TailoredCertification] = Field(
        default_factory=list,
        description="Certifications"
    )
    projects: list[TailoredProject] = Field(
        default_factory=list,
        description="Projects section"
    )


class ChangeLogEntry(BaseModel):
    """A single change made during tailoring."""
    
    section: str = Field(..., description="Section where change occurred")
    change_type: Literal["reorder", "rewrite", "add_keyword", "quantify", "remove"] = Field(
        ..., description="Type of change"
    )
    original: Optional[str] = Field(default=None, description="Original content")
    new: str = Field(..., description="New content")
    justification: str = Field(..., description="Why this change was made")
    confidence: Literal["high", "medium", "low"] = Field(
        ..., description="Confidence in this change"
    )
    requires_review: bool = Field(
        default=False,
        description="Whether user should review this"
    )


class BorderlineItem(BaseModel):
    """An item that needs user review."""
    
    content: str = Field(..., description="The content in question")
    category: Literal["inferred_but_reasonable", "reframed_significantly", "gap_mitigation"] = Field(
        ..., description="Category of borderline content"
    )
    original_evidence: str = Field(..., description="What this is based on")
    risk_level: Literal["low", "medium", "high"] = Field(
        ..., description="Risk level"
    )
    user_prompt: str = Field(..., description="Question for user confirmation")


class CoverLetter(BaseModel):
    """Generated cover letter."""
    
    hook: str = Field(..., description="Opening paragraph")
    value_proposition: str = Field(..., description="Main body paragraph")
    fit_narrative: str = Field(..., description="Why you're a good fit")
    closing: str = Field(..., description="Closing paragraph")
    
    @property
    def full_text(self) -> str:
        """Get the complete cover letter text."""
        return f"{self.hook}\n\n{self.value_proposition}\n\n{self.fit_narrative}\n\n{self.closing}"


class MatchScoreBreakdown(BaseModel):
    """Breakdown of the match score calculation."""
    
    must_have_component: float = Field(..., description="Score from must-have matches")
    nice_to_have_component: float = Field(..., description="Score from nice-to-have matches")
    bonuses: list[str] = Field(default_factory=list, description="Score bonuses applied")
    penalties: list[str] = Field(default_factory=list, description="Score penalties applied")


class MatchScore(BaseModel):
    """Match score with explanation."""
    
    score: int = Field(..., ge=0, le=100, description="Final score")
    breakdown: MatchScoreBreakdown = Field(..., description="Score breakdown")
    explanation: str = Field(..., description="Human-readable explanation")


class TailorResult(BaseModel):
    """Complete result of CV tailoring."""
    
    tailored_cv: TailoredCV = Field(..., description="The tailored CV")
    cover_letter: Optional[CoverLetter] = Field(
        default=None,
        description="Generated cover letter"
    )
    changes_log: list[ChangeLogEntry] = Field(
        default_factory=list,
        description="All changes made"
    )
    borderline_items: list[BorderlineItem] = Field(
        default_factory=list,
        description="Items requiring user review"
    )
    match_score: MatchScore = Field(..., description="Match score")
    
    # Include analysis data
    mapping_summary: Optional[dict] = Field(
        default=None,
        description="Summary of requirement-evidence mapping"
    )
