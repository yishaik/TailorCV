"""
Module 5: Quality Assurance (Guardrails)

Validates output integrity and flags potential issues.
Ensures no fabrication and proper traceability.
"""
from typing import Optional
from ..models.cv_facts import CVFacts
from ..models.output import (
    TailoredCV,
    ChangeLogEntry,
    BorderlineItem,
    MatchScore,
    MatchScoreBreakdown
)
from ..models.mapping import MappingResult
import logging
import re

logger = logging.getLogger(__name__)


class QAValidationError(Exception):
    """Raised when fabrication is detected."""
    pass


class QAValidator:
    """Validates tailored CV against original facts."""
    
    def __init__(self, original_cv: CVFacts, tailored_cv: TailoredCV):
        self.original = original_cv
        self.tailored = tailored_cv
        self.issues: list[str] = []
        self.warnings: list[str] = []
    
    def validate_all(self) -> tuple[bool, list[str], list[str]]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self._check_fabricated_companies()
        self._check_fabricated_skills()
        self._check_exaggerated_metrics()
        self._check_title_changes()
        
        is_valid = len(self.issues) == 0
        return is_valid, self.issues, self.warnings
    
    def _check_fabricated_companies(self):
        """Ensure all companies in output exist in original."""
        original_companies = {exp.company.lower() for exp in self.original.experience}
        
        for exp in self.tailored.experience:
            if exp.company.lower() not in original_companies:
                self.issues.append(
                    f"FABRICATION: Company '{exp.company}' not found in original CV"
                )
    
    def _check_fabricated_skills(self):
        """Check for skills not evidenced in original CV."""
        # Gather all original skills and technologies
        original_skills = set()
        
        for skill in self.original.skills.explicitly_listed:
            original_skills.add(skill.lower())
        
        for skill in self.original.skills.inferred_from_experience:
            original_skills.add(skill.skill.lower())
        
        for exp in self.original.experience:
            for resp in exp.responsibilities:
                for tech in resp.extracted_facts.technologies:
                    original_skills.add(tech.lower())
        
        for proj in self.original.projects:
            for tech in proj.technologies:
                original_skills.add(tech.lower())
        
        # Check tailored skills
        tailored_skills = set()
        tailored_skills.update(s.lower() for s in self.tailored.skills.primary)
        tailored_skills.update(s.lower() for s in self.tailored.skills.secondary)
        tailored_skills.update(s.lower() for s in self.tailored.skills.tools)
        
        fabricated = tailored_skills - original_skills
        if fabricated:
            for skill in fabricated:
                self.issues.append(
                    f"FABRICATION: Skill '{skill}' not evidenced in original CV"
                )
    
    def _check_exaggerated_metrics(self):
        """Check for inflated numbers in bullets."""
        # Extract numbers from original
        original_numbers = self._extract_numbers_from_cv()
        
        # Check tailored bullets for numbers
        for exp in self.tailored.experience:
            for bullet in exp.bullets:
                bullet_numbers = self._extract_numbers(bullet.text)
                for num in bullet_numbers:
                    # Check if this number exists in original or is close
                    if not self._number_is_valid(num, original_numbers):
                        self.warnings.append(
                            f"POSSIBLE EXAGGERATION: Number '{num}' in bullet may not match original"
                        )
    
    def _extract_numbers_from_cv(self) -> set:
        """Extract all numbers from original CV."""
        numbers = set()
        
        for exp in self.original.experience:
            for resp in exp.responsibilities:
                numbers.update(self._extract_numbers(resp.original_text))
            for ach in exp.achievements:
                numbers.update(self._extract_numbers(ach.original_text))
                if ach.metrics:
                    numbers.add(ach.metrics.value)
        
        return numbers
    
    def _extract_numbers(self, text: str) -> list[str]:
        """Extract number-like patterns from text."""
        patterns = [
            r'\d+%',          # Percentages
            r'\$[\d,]+',      # Currency
            r'\d+[+]?',       # Plain numbers
            r'\d+[kKmM]',     # Abbreviated numbers
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)
        
        return numbers
    
    def _number_is_valid(self, num: str, original_numbers: set) -> bool:
        """Check if a number is valid based on original CV."""
        # Direct match
        if num in original_numbers:
            return True
        
        # Try to parse and compare
        try:
            # Extract numeric value
            num_clean = re.sub(r'[^\d.]', '', num)
            if not num_clean:
                return True  # Can't parse, assume valid
            
            num_val = float(num_clean)
            
            for orig in original_numbers:
                orig_clean = re.sub(r'[^\d.]', '', orig)
                if orig_clean:
                    orig_val = float(orig_clean)
                    # Allow if same or slightly lower (rounding)
                    if orig_val * 0.9 <= num_val <= orig_val * 1.1:
                        return True
        except ValueError:
            pass
        
        return False
    
    def _check_title_changes(self):
        """Check for inappropriate title changes."""
        if not self.original.experience:
            return
        
        original_title = self.original.experience[0].title.lower()
        tailored_title = self.tailored.header.title.lower()
        
        # Flag significant title changes
        promotion_words = ['senior', 'lead', 'principal', 'director', 'head', 'chief', 'vp']
        
        for word in promotion_words:
            if word in tailored_title and word not in original_title:
                self.warnings.append(
                    f"TITLE CHANGE: Added '{word}' to title - verify this is accurate"
                )


def detect_fabrication(original_cv: CVFacts, tailored_cv: TailoredCV) -> tuple[bool, list[str]]:
    """
    Detect any fabrication in the tailored CV.
    
    Args:
        original_cv: Original CV facts
        tailored_cv: Generated tailored CV
    
    Returns:
        Tuple of (has_fabrication, list of fabrication details)
    """
    validator = QAValidator(original_cv, tailored_cv)
    is_valid, errors, _ = validator.validate_all()
    return not is_valid, errors


def detect_exaggeration(changes_log: list[ChangeLogEntry]) -> list[BorderlineItem]:
    """
    Detect potential exaggerations in changes.
    
    Args:
        changes_log: Log of all changes made
    
    Returns:
        List of borderline items flagged for review
    """
    borderline = []
    
    for change in changes_log:
        if change.change_type == "rewrite" and change.original:
            # Check for scope escalation
            scope_words = {
                'assisted': 'led',
                'helped': 'managed',
                'participated': 'drove',
                'contributed': 'owned',
                'supported': 'executed'
            }
            
            original_lower = change.original.lower()
            new_lower = change.new.lower()
            
            for weak, strong in scope_words.items():
                if weak in original_lower and strong in new_lower:
                    borderline.append(BorderlineItem(
                        content=change.new,
                        category="reframed_significantly",
                        original_evidence=change.original,
                        risk_level="medium",
                        user_prompt=f"Original used '{weak}', now uses '{strong}'. Is this accurate?"
                    ))
                    break
    
    return borderline


def calculate_match_score(
    mapping: MappingResult,
    changes_log: list[ChangeLogEntry],
    borderline_items: list[BorderlineItem]
) -> MatchScore:
    """
    Calculate final match score with adjustments.
    
    Args:
        mapping: Requirement-to-evidence mapping
        changes_log: Log of changes made
        borderline_items: Items flagged for review
    
    Returns:
        Final match score with breakdown
    """
    base_score = mapping.overall_match.score
    bonuses = []
    penalties = []
    
    # Bonus for quantified achievements aligned with job
    quantified_count = sum(
        1 for change in changes_log 
        if change.section == "experience" and any(c.isdigit() for c in change.new)
    )
    if quantified_count >= 3:
        bonuses.append(f"+5 for {quantified_count} quantified achievements")
        base_score += 5
    
    # Bonus for keyword integration
    keyword_changes = [
        c for c in changes_log 
        if c.change_type == "add_keyword" or "keyword" in c.justification.lower()
    ]
    if keyword_changes:
        bonuses.append(f"+3 for keyword integration in {len(keyword_changes)} bullets")
        base_score += 3
    
    # Penalty for critical gaps
    critical_gaps = len(mapping.overall_match.critical_gaps)
    if critical_gaps > 0:
        penalty = min(critical_gaps * 10, 30)
        penalties.append(f"-{penalty} for {critical_gaps} critical gaps")
        base_score -= penalty
    
    # Penalty for items requiring review
    if len(borderline_items) > 3:
        penalties.append(f"-5 for {len(borderline_items)} items requiring review")
        base_score -= 5
    
    # Ensure score stays in range
    final_score = max(0, min(100, base_score))
    
    # Parse coverage for breakdown
    must_have_parts = mapping.overall_match.must_have_coverage.split("/")
    nice_to_have_parts = mapping.overall_match.nice_to_have_coverage.split("/")
    
    must_have_pct = (int(must_have_parts[0]) / int(must_have_parts[1]) * 70) if int(must_have_parts[1]) > 0 else 70
    nice_to_have_pct = (int(nice_to_have_parts[0]) / int(nice_to_have_parts[1]) * 30) if int(nice_to_have_parts[1]) > 0 else 30
    
    breakdown = MatchScoreBreakdown(
        must_have_component=must_have_pct,
        nice_to_have_component=nice_to_have_pct,
        bonuses=bonuses,
        penalties=penalties
    )
    
    # Generate explanation
    if final_score >= 80:
        explanation = "Strong match - candidate meets most requirements"
    elif final_score >= 60:
        explanation = "Good match - candidate meets core requirements with some gaps"
    elif final_score >= 40:
        explanation = "Moderate match - significant gaps but transferable experience"
    else:
        explanation = "Low match - consider if this role is appropriate"
    
    if mapping.overall_match.critical_gaps:
        explanation += f". Critical gaps: {', '.join(mapping.overall_match.critical_gaps[:3])}"
    
    return MatchScore(
        score=final_score,
        breakdown=breakdown,
        explanation=explanation
    )


def run_quality_checks(
    original_cv: CVFacts,
    tailored_cv: TailoredCV,
    mapping: MappingResult,
    changes_log: list[ChangeLogEntry],
    borderline_items: list[BorderlineItem]
) -> tuple[bool, list[str], list[str], MatchScore]:
    """
    Run all quality checks on the tailored CV.
    
    Args:
        original_cv: Original CV facts
        tailored_cv: Generated tailored CV
        mapping: Requirement-to-evidence mapping
        changes_log: Log of changes made
        borderline_items: Items flagged for review
    
    Returns:
        Tuple of (is_valid, errors, warnings, match_score)
    """
    # Run fabrication checks
    validator = QAValidator(original_cv, tailored_cv)
    is_valid, errors, warnings = validator.validate_all()
    
    # Detect exaggerations
    exaggeration_items = detect_exaggeration(changes_log)
    borderline_items.extend(exaggeration_items)
    
    # Calculate final score
    match_score = calculate_match_score(mapping, changes_log, borderline_items)
    
    # Add warnings for low score
    if match_score.score < 50:
        warnings.append("LOW_MATCH_SCORE: Match score below 50%, consider if role is appropriate")
    
    if len(borderline_items) > 5:
        warnings.append(f"MANY_BORDERLINE_ITEMS: {len(borderline_items)} items require user review")
    
    return is_valid, errors, warnings, match_score
