"""
Pydantic models for tailoring options and request/response structures.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional


class TailorOptions(BaseModel):
    """Options for CV tailoring process."""
    
    generate_cover_letter: bool = Field(
        default=True,
        description="Whether to generate a cover letter"
    )
    output_format: Literal["docx", "pdf", "markdown", "json"] = Field(
        default="markdown",
        description="Output format for the tailored CV"
    )
    language: str = Field(
        default="en",
        description="Language code for output"
    )
    strictness_level: Literal["conservative", "moderate", "aggressive"] = Field(
        default="moderate",
        description="How aggressively to tailor the CV"
    )


class TailorRequest(BaseModel):
    """Request model for the main tailor endpoint."""
    
    job_description: str = Field(
        ...,
        min_length=50,
        description="The job description to tailor the CV for"
    )
    original_cv: str = Field(
        ...,
        min_length=100,
        description="The original CV text or content"
    )
    options: TailorOptions = Field(
        default_factory=TailorOptions,
        description="Tailoring options"
    )


class StrictnessConfig(BaseModel):
    """Configuration for each strictness level."""
    
    allow_inferred_skills: bool
    allow_reframing: Literal["minimal", "with_same_facts", "extensive"]
    keyword_injection: Literal["only_if_evidenced", "natural_integration", "maximize_ats"]
    gap_mitigation: Literal["acknowledge_only", "all_strategies", "creative_positioning"]


# Strictness level presets
STRICTNESS_CONFIGS = {
    "conservative": StrictnessConfig(
        allow_inferred_skills=False,
        allow_reframing="minimal",
        keyword_injection="only_if_evidenced",
        gap_mitigation="acknowledge_only"
    ),
    "moderate": StrictnessConfig(
        allow_inferred_skills=True,
        allow_reframing="with_same_facts",
        keyword_injection="natural_integration",
        gap_mitigation="all_strategies"
    ),
    "aggressive": StrictnessConfig(
        allow_inferred_skills=True,
        allow_reframing="extensive",
        keyword_injection="maximize_ats",
        gap_mitigation="creative_positioning"
    )
}
