"""
Tests for QA guardrails — fabrication detection, exaggeration checks, scoring.
"""
import pytest

from app.services.qa_guardrails import (
    QAValidator,
    detect_fabrication,
    detect_exaggeration,
    calculate_match_score,
    run_quality_checks,
)
from app.models.output import (
    TailoredCV, TailoredHeader, TailoredExperience,
    TailoredExperienceBullet, TailoredSkills,
    ChangeLogEntry, BorderlineItem,
)
from tests.conftest import (
    make_cv_facts, make_mapping, make_tailored_cv,
    make_match_score,
)


# ===================================================================
# Fabrication detection
# ===================================================================

class TestFabricationDetection:
    def test_no_fabrication(self):
        cv = make_cv_facts()
        tailored = make_tailored_cv(
            skills=TailoredSkills(
                primary=["Python", "FastAPI"],  # Only explicitly listed skills
                secondary=["Docker"],
                tools=[],
            ),
        )
        validator = QAValidator(cv, tailored)
        is_valid, errors, warnings = validator.validate_all()
        assert is_valid, f"Unexpected errors: {errors}"

    def test_fabricated_company(self):
        cv = make_cv_facts()
        tailored = make_tailored_cv(
            experience=[
                TailoredExperience(
                    company="Fake Corp",  # Not in original CV
                    title="Engineer",
                    dates="2020-Present",
                    bullets=[],
                ),
            ],
        )
        has_fab, errors = detect_fabrication(cv, tailored)
        assert has_fab
        assert any("Fake Corp" in e for e in errors)

    def test_fabricated_skill(self):
        cv = make_cv_facts()
        tailored = make_tailored_cv(
            skills=TailoredSkills(
                primary=["Rust", "Haskell"],  # Not in original
                secondary=[],
                tools=[],
            ),
        )
        has_fab, errors = detect_fabrication(cv, tailored)
        assert has_fab
        assert any("rust" in e.lower() for e in errors)

    def test_valid_skill_from_original(self):
        cv = make_cv_facts()
        tailored = make_tailored_cv(
            skills=TailoredSkills(
                primary=["Python", "FastAPI", "Docker"],  # All in explicitly_listed
                secondary=[],
                tools=[],
            ),
        )
        has_fab, errors = detect_fabrication(cv, tailored)
        assert not has_fab, f"Unexpected fabrication: {errors}"


# ===================================================================
# Exaggeration detection
# ===================================================================

class TestExaggerationDetection:
    def test_scope_escalation(self):
        changes = [
            ChangeLogEntry(
                section="experience",
                change_type="rewrite",
                original="Assisted with building APIs",
                new="Led the design and architecture of APIs",
                justification="Reframed for impact",
                confidence="medium",
            ),
        ]
        borderline = detect_exaggeration(changes)
        assert len(borderline) >= 1
        assert borderline[0].category == "reframed_significantly"

    def test_no_exaggeration_on_minor_edit(self):
        changes = [
            ChangeLogEntry(
                section="experience",
                change_type="rewrite",
                original="Built REST APIs",
                new="Built scalable REST APIs",
                justification="Added detail",
                confidence="high",
            ),
        ]
        borderline = detect_exaggeration(changes)
        assert len(borderline) == 0

    def test_keyword_addition_not_flagged(self):
        changes = [
            ChangeLogEntry(
                section="skills",
                change_type="add_keyword",
                original="",
                new="Python",
                justification="Keyword already in skills",
                confidence="high",
            ),
        ]
        borderline = detect_exaggeration(changes)
        assert len(borderline) == 0


# ===================================================================
# Match score calculation
# ===================================================================

class TestMatchScoreCalculation:
    def test_basic_score(self):
        mapping = make_mapping()
        score = calculate_match_score(mapping, [], [])
        assert 0 <= score.score <= 100
        assert score.explanation  # Has an explanation

    def test_bonus_for_quantified_achievements(self):
        mapping = make_mapping()
        changes = [
            ChangeLogEntry(
                section="experience",
                change_type="rewrite",
                original="Built things",
                new="Built system handling 1000 requests/sec",
                justification="Added metrics",
                confidence="high",
            ),
            ChangeLogEntry(
                section="experience",
                change_type="rewrite",
                original="Improved performance",
                new="Improved performance by 40%",
                justification="Added metrics",
                confidence="high",
            ),
            ChangeLogEntry(
                section="experience",
                change_type="rewrite",
                original="Managed team",
                new="Managed team of 5 engineers",
                justification="Added metrics",
                confidence="high",
            ),
        ]
        score = calculate_match_score(mapping, changes, [])
        assert any("quantified" in b.lower() for b in score.breakdown.bonuses)

    def test_penalty_for_critical_gaps(self):
        mapping = make_mapping(
            overall_match=make_mapping().overall_match.model_copy(
                update={"critical_gaps": ["Kubernetes", "AWS", "CI/CD"]}
            ),
        )
        score = calculate_match_score(mapping, [], [])
        assert any("gap" in p.lower() for p in score.breakdown.penalties)

    def test_score_clamped_0_100(self):
        mapping = make_mapping(
            overall_match=make_mapping().overall_match.model_copy(update={"score": 200}),
        )
        score = calculate_match_score(mapping, [], [])
        assert 0 <= score.score <= 100


# ===================================================================
# Full quality check pipeline
# ===================================================================

class TestRunQualityChecks:
    def test_clean_pass(self):
        cv = make_cv_facts()
        tailored = make_tailored_cv(
            skills=TailoredSkills(primary=["Python", "FastAPI", "Docker"], secondary=[], tools=[]),
        )
        mapping = make_mapping()
        is_valid, errors, warnings, score = run_quality_checks(cv, tailored, mapping, [], [])
        assert is_valid, f"Unexpected errors: {errors}"
        assert score.score > 0

    def test_fabrication_fails(self):
        cv = make_cv_facts()
        tailored = make_tailored_cv(
            skills=TailoredSkills(primary=["COBOL"], secondary=[], tools=[]),
        )
        mapping = make_mapping()
        is_valid, errors, warnings, score = run_quality_checks(cv, tailored, mapping, [], [])
        assert not is_valid
        assert len(errors) > 0
