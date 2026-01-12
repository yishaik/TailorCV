"""
Module 3: Requirements-to-Evidence Mapper

Creates explicit mapping between job requirements and CV evidence.
"""
from typing import Optional
from ..models.job_requirements import JobRequirements, Requirement, RequirementCategory
from ..models.cv_facts import CVFacts
from ..models.mapping import (
    MappingResult,
    MappingEntry,
    RequirementRef,
    EvidenceItem,
    GapAnalysis,
    MitigationOption,
    OverallMatch,
    KeywordCoverage
)
from ..models.options import StrictnessConfig, STRICTNESS_CONFIGS
from .cv_extractor import get_skill_evidence, get_all_skills, get_total_experience_years
from .job_extractor import get_keyword_priority_map
from ..utils.llm_client import get_llm_client
import logging

logger = logging.getLogger(__name__)


SIMILARITY_THRESHOLD = 0.6  # Threshold for considering skills as related


async def map_requirements_to_evidence(
    requirements: JobRequirements,
    cv_facts: CVFacts,
    strictness: str = "moderate"
) -> MappingResult:
    """
    Map job requirements to CV evidence.
    
    Args:
        requirements: Parsed job requirements
        cv_facts: Parsed CV facts
        strictness: Strictness level for matching
    
    Returns:
        Complete mapping result with scores
    """
    config = STRICTNESS_CONFIGS.get(strictness, STRICTNESS_CONFIGS["moderate"])
    
    mapping_table = []
    
    # Process must-have requirements
    for req in requirements.must_have:
        entry = await _create_mapping_entry(req, "must_have", cv_facts, config)
        mapping_table.append(entry)
    
    # Process nice-to-have requirements
    for req in requirements.nice_to_have:
        entry = await _create_mapping_entry(req, "nice_to_have", cv_facts, config)
        mapping_table.append(entry)
    
    # Calculate overall match
    overall_match = _calculate_overall_match(mapping_table, requirements)
    
    # Analyze keyword coverage
    keyword_coverage = _analyze_keyword_coverage(requirements, cv_facts)
    
    return MappingResult(
        mapping_table=mapping_table,
        overall_match=overall_match,
        keyword_coverage=keyword_coverage
    )


async def _create_mapping_entry(
    requirement: Requirement,
    priority: str,
    cv_facts: CVFacts,
    config: StrictnessConfig
) -> MappingEntry:
    """Create a mapping entry for a single requirement."""
    
    req_ref = RequirementRef(
        text=requirement.description,
        priority=priority,
        category=requirement.category.value
    )
    
    # Find evidence for this requirement
    evidence_items = []
    
    # Check each keyword in the requirement
    for keyword in requirement.keywords:
        keyword_evidence = get_skill_evidence(cv_facts, keyword)
        
        for ev in keyword_evidence:
            evidence_items.append(EvidenceItem(
                source_type=ev.get("source_type", "skill"),
                source_id=ev.get("source_id", ""),
                original_text=ev.get("text", ""),
                relevance_score=_calculate_relevance_score(keyword, ev),
                match_type="direct"
            ))
    
    # Check for transferable skills if allowed
    if config.allow_inferred_skills and not evidence_items:
        transferable = await _find_transferable_evidence(requirement, cv_facts)
        evidence_items.extend(transferable)
    
    # Check experience requirements
    if requirement.category == RequirementCategory.EXPERIENCE:
        exp_evidence = _check_experience_requirement(requirement, cv_facts)
        if exp_evidence:
            evidence_items.append(exp_evidence)
    
    # Deduplicate evidence
    seen_texts = set()
    unique_evidence = []
    for ev in evidence_items:
        if ev.original_text not in seen_texts:
            seen_texts.add(ev.original_text)
            unique_evidence.append(ev)
    
    # Perform gap analysis
    gap_analysis = _analyze_gap(requirement, unique_evidence, config)
    
    return MappingEntry(
        requirement=req_ref,
        evidence=unique_evidence,
        gap_analysis=gap_analysis
    )


def _calculate_relevance_score(keyword: str, evidence: dict) -> int:
    """Calculate relevance score for an evidence item."""
    base_score = 70
    
    # Bonus for exact keyword match in text
    if keyword.lower() in evidence.get("text", "").lower():
        base_score += 20
    
    # Bonus for experience source (most valuable)
    if evidence.get("source_type") == "experience":
        base_score += 10
    elif evidence.get("source_type") == "certification":
        base_score += 5
    
    return min(base_score, 100)


async def _find_transferable_evidence(
    requirement: Requirement,
    cv_facts: CVFacts
) -> list[EvidenceItem]:
    """Find transferable skills that could satisfy the requirement."""
    client = get_llm_client()
    
    all_skills = get_all_skills(cv_facts)
    
    # Use LLM to find related skills
    prompt = f"""
    The job requires: {requirement.description}
    Keywords: {', '.join(requirement.keywords)}
    
    Candidate has these skills: {', '.join(all_skills)}
    
    Identify any skills the candidate has that are TRANSFERABLE to this requirement.
    Only include genuinely related skills (e.g., AWS for Azure cloud experience).
    
    Return a JSON object with:
    {{
        "transferable_skills": [
            {{"candidate_skill": "string", "relevance_explanation": "string"}}
        ]
    }}
    
    Return an empty list if no skills are transferable.
    """
    
    try:
        response = await client.generate_text(prompt)
        import json
        
        # Try to parse JSON from response
        if "{" in response:
            start = response.index("{")
            end = response.rindex("}") + 1
            data = json.loads(response[start:end])
            
            evidence_items = []
            for skill_info in data.get("transferable_skills", []):
                skill_name = skill_info.get("candidate_skill", "")
                if skill_name:
                    skill_evidence = get_skill_evidence(cv_facts, skill_name)
                    for ev in skill_evidence[:1]:  # Take first evidence
                        evidence_items.append(EvidenceItem(
                            source_type=ev.get("source_type", "skill"),
                            source_id=ev.get("source_id", ""),
                            original_text=f"{ev.get('text', '')} (Transferable: {skill_info.get('relevance_explanation', '')})",
                            relevance_score=50,  # Lower score for transferable
                            match_type="transferable"
                        ))
            
            return evidence_items
    except Exception as e:
        logger.warning(f"Failed to find transferable skills: {e}")
    
    return []


def _check_experience_requirement(requirement: Requirement, cv_facts: CVFacts) -> Optional[EvidenceItem]:
    """Check if experience requirement is met."""
    if requirement.years_required:
        total_years = get_total_experience_years(cv_facts)
        
        if total_years >= requirement.years_required:
            return EvidenceItem(
                source_type="experience",
                source_id="total",
                original_text=f"Total experience: {total_years} years",
                relevance_score=100,
                match_type="direct"
            )
        elif total_years >= requirement.years_required * 0.7:
            return EvidenceItem(
                source_type="experience",
                source_id="total",
                original_text=f"Total experience: {total_years} years (requirement: {requirement.years_required})",
                relevance_score=60,
                match_type="partial"
            )
    
    return None


def _analyze_gap(
    requirement: Requirement,
    evidence: list[EvidenceItem],
    config: StrictnessConfig
) -> GapAnalysis:
    """Analyze the gap between requirement and evidence."""
    
    if not evidence:
        # No evidence found - this is a gap
        severity = "critical" if requirement.specificity == "exact" else "moderate"
        
        mitigation_options = []
        
        if config.gap_mitigation in ["all_strategies", "creative_positioning"]:
            mitigation_options.append(MitigationOption(
                strategy="acknowledge_gap",
                suggestion=f"Acknowledge this gap and express willingness to learn",
                requires_user_confirmation=True
            ))
            
            if config.gap_mitigation == "creative_positioning":
                mitigation_options.append(MitigationOption(
                    strategy="show_adjacent",
                    suggestion=f"Highlight quick learning ability through similar transitions in past",
                    requires_user_confirmation=True
                ))
        
        return GapAnalysis(
            has_gap=True,
            gap_severity=severity,
            mitigation_options=mitigation_options
        )
    
    # Check if we have strong evidence
    max_score = max(ev.relevance_score for ev in evidence)
    has_direct_match = any(ev.match_type == "direct" for ev in evidence)
    
    if max_score >= 80 and has_direct_match:
        return GapAnalysis(has_gap=False, gap_severity="none", mitigation_options=[])
    elif max_score >= 50:
        return GapAnalysis(
            has_gap=True,
            gap_severity="minor",
            mitigation_options=[
                MitigationOption(
                    strategy="reframe_existing",
                    suggestion="Reframe existing experience to better match requirement language",
                    requires_user_confirmation=False
                )
            ]
        )
    else:
        return GapAnalysis(
            has_gap=True,
            gap_severity="moderate",
            mitigation_options=[
                MitigationOption(
                    strategy="highlight_learning",
                    suggestion="Emphasize related experience and quick learning capability",
                    requires_user_confirmation=True
                )
            ]
        )


def _calculate_overall_match(mapping_table: list[MappingEntry], requirements: JobRequirements) -> OverallMatch:
    """Calculate overall match score."""
    
    must_have_entries = [e for e in mapping_table if e.requirement.priority == "must_have"]
    nice_to_have_entries = [e for e in mapping_table if e.requirement.priority == "nice_to_have"]
    
    # Count matches
    must_have_matches = sum(1 for e in must_have_entries if not e.gap_analysis.has_gap or e.gap_analysis.gap_severity == "minor")
    nice_to_have_matches = sum(1 for e in nice_to_have_entries if not e.gap_analysis.has_gap or e.gap_analysis.gap_severity == "minor")
    
    total_must_have = len(must_have_entries)
    total_nice_to_have = len(nice_to_have_entries)
    
    # Calculate score (must-have weighted 70%, nice-to-have 30%)
    must_have_pct = (must_have_matches / total_must_have * 100) if total_must_have > 0 else 100
    nice_to_have_pct = (nice_to_have_matches / total_nice_to_have * 100) if total_nice_to_have > 0 else 100
    
    base_score = int(must_have_pct * 0.7 + nice_to_have_pct * 0.3)
    
    # Find strongest matches and critical gaps
    strongest = []
    critical_gaps = []
    
    for entry in mapping_table:
        if entry.evidence and max((e.relevance_score for e in entry.evidence), default=0) >= 80:
            strongest.append(entry.requirement.text[:50])
        
        if entry.gap_analysis.gap_severity == "critical":
            critical_gaps.append(entry.requirement.text[:50])
    
    return OverallMatch(
        score=min(base_score, 100),
        must_have_coverage=f"{must_have_matches}/{total_must_have}",
        nice_to_have_coverage=f"{nice_to_have_matches}/{total_nice_to_have}",
        strongest_matches=strongest[:5],
        critical_gaps=critical_gaps[:5]
    )


def _analyze_keyword_coverage(requirements: JobRequirements, cv_facts: CVFacts) -> KeywordCoverage:
    """Analyze ATS keyword coverage."""
    
    all_keywords = set()
    all_keywords.update(requirements.ats_keywords.high_priority)
    all_keywords.update(requirements.ats_keywords.medium_priority)
    all_keywords.update(requirements.ats_keywords.contextual)
    
    cv_skills = set(s.lower() for s in get_all_skills(cv_facts))
    
    present = []
    addressable = []
    missing = []
    
    for keyword in all_keywords:
        keyword_lower = keyword.lower()
        
        if keyword_lower in cv_skills:
            present.append(keyword)
        elif get_skill_evidence(cv_facts, keyword):
            present.append(keyword)
        else:
            # Check if we can address this through related experience
            # For now, mark as genuinely missing
            missing.append(keyword)
    
    return KeywordCoverage(
        present_in_cv=present,
        missing_but_addressable=addressable,
        genuinely_missing=missing
    )
