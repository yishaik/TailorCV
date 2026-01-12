"""
Pydantic models for requirements-to-evidence mapping.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional


class EvidenceItem(BaseModel):
    """Evidence from CV that supports a requirement."""
    
    source_type: Literal["experience", "skill", "project", "certification", "education"] = Field(
        ..., description="Type of source in CV"
    )
    source_id: str = Field(..., description="ID of the source item")
    original_text: str = Field(..., description="Original text from CV")
    relevance_score: int = Field(
        ..., ge=0, le=100,
        description="How relevant this evidence is (0-100)"
    )
    match_type: Literal["direct", "transferable", "partial", "learning"] = Field(
        ..., description="Type of match"
    )


class MitigationOption(BaseModel):
    """Strategy to mitigate a gap in requirements."""
    
    strategy: Literal["reframe_existing", "highlight_learning", "show_adjacent", "acknowledge_gap"] = Field(
        ..., description="Mitigation strategy type"
    )
    suggestion: str = Field(..., description="Specific suggestion for addressing the gap")
    requires_user_confirmation: bool = Field(
        default=False,
        description="Whether this needs user confirmation"
    )


class GapAnalysis(BaseModel):
    """Analysis of a gap between requirement and CV."""
    
    has_gap: bool = Field(..., description="Whether there is a gap")
    gap_severity: Literal["critical", "moderate", "minor", "none"] = Field(
        ..., description="Severity of the gap"
    )
    mitigation_options: list[MitigationOption] = Field(
        default_factory=list,
        description="Options to mitigate the gap"
    )


class RequirementRef(BaseModel):
    """Reference to a job requirement."""
    
    text: str = Field(..., description="Requirement text")
    priority: Literal["must_have", "nice_to_have", "inferred"] = Field(
        ..., description="Priority level"
    )
    category: str = Field(..., description="Requirement category")


class MappingEntry(BaseModel):
    """A single mapping between requirement and evidence."""
    
    requirement: RequirementRef = Field(..., description="The requirement")
    evidence: list[EvidenceItem] = Field(
        default_factory=list,
        description="Evidence supporting this requirement"
    )
    gap_analysis: GapAnalysis = Field(..., description="Gap analysis for this requirement")


class OverallMatch(BaseModel):
    """Overall match statistics."""
    
    score: int = Field(..., ge=0, le=100, description="Overall match score")
    must_have_coverage: str = Field(..., description="X/Y format coverage")
    nice_to_have_coverage: str = Field(..., description="X/Y format coverage")
    strongest_matches: list[str] = Field(
        default_factory=list,
        description="Best matching areas"
    )
    critical_gaps: list[str] = Field(
        default_factory=list,
        description="Critical missing requirements"
    )


class KeywordCoverage(BaseModel):
    """ATS keyword coverage analysis."""
    
    present_in_cv: list[str] = Field(
        default_factory=list,
        description="Keywords already in CV"
    )
    missing_but_addressable: list[str] = Field(
        default_factory=list,
        description="Keywords that can be added based on real experience"
    )
    genuinely_missing: list[str] = Field(
        default_factory=list,
        description="Keywords that cannot be ethically added"
    )


class MappingResult(BaseModel):
    """Complete mapping result."""
    
    mapping_table: list[MappingEntry] = Field(
        default_factory=list,
        description="All requirement-evidence mappings"
    )
    overall_match: OverallMatch = Field(..., description="Overall match statistics")
    keyword_coverage: KeywordCoverage = Field(
        default_factory=KeywordCoverage,
        description="Keyword coverage analysis"
    )
