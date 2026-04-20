"""
Tests for the shared tailoring pipeline.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.tailoring_pipeline import run_tailoring_pipeline, TailoringError
from app.models.options import TailorRequest, TailorOptions
from tests.conftest import (
    make_cv_facts, make_job_requirements, make_mapping,
    make_tailored_cv, make_match_score, JOB_DESCRIPTION, CV_TEXT,
)


@pytest.fixture
def pipeline_request():
    return TailorRequest(
        job_description=JOB_DESCRIPTION,
        original_cv=CV_TEXT,
        options=TailorOptions(),
    )


def _mock_pipeline_services():
    """Return a dict of mocked service functions."""
    return {
        "app.services.tailoring_pipeline.extract_job_requirements": AsyncMock(return_value=make_job_requirements()),
        "app.services.tailoring_pipeline.extract_cv_facts": AsyncMock(return_value=make_cv_facts()),
        "app.services.tailoring_pipeline.map_requirements_to_evidence": AsyncMock(return_value=make_mapping()),
        "app.services.tailoring_pipeline.generate_tailored_cv": AsyncMock(return_value=(make_tailored_cv(), [], [])),
        "app.services.tailoring_pipeline.run_quality_checks": MagicMock(return_value=(True, [], [], make_match_score())),
        "app.services.tailoring_pipeline.generate_cover_letter": AsyncMock(return_value=None),
    }


class TestTailoringPipeline:
    @pytest.mark.anyio
    async def test_successful_run(self, pipeline_request):
        mocks = _mock_pipeline_services()
        with patch.dict("sys.modules", {}):
            for target, mock in mocks.items():
                patcher = patch(target, mock)
                patcher.start()
            try:
                result = await run_tailoring_pipeline(pipeline_request)
            finally:
                for target in mocks:
                    patch(target, mocks[target]).stop()

        assert result.tailored_cv.header.name == "Jane Doe"
        assert result.match_score.score == 75

    @pytest.mark.anyio
    async def test_progress_callback(self, pipeline_request):
        steps = []

        def on_step(step, total, msg):
            steps.append((step, total, msg))

        mocks = _mock_pipeline_services()
        patchers = [patch(t, m) for t, m in mocks.items()]
        for p in patchers:
            p.start()
        try:
            await run_tailoring_pipeline(pipeline_request, on_step=on_step)
        finally:
            for p in patchers:
                p.stop()

        # Should have 6 progress callbacks (no cover letter)
        assert len(steps) == 6
        assert steps[0][0] == 1
        assert steps[-1][0] == 6

    @pytest.mark.anyio
    async def test_fabrication_raises_error(self, pipeline_request):
        mocks = _mock_pipeline_services()
        # Override quality checks to return failure
        mocks["app.services.tailoring_pipeline.run_quality_checks"] = MagicMock(
            return_value=(False, ["Fabricated company"], [], make_match_score())
        )
        patchers = [patch(t, m) for t, m in mocks.items()]
        for p in patchers:
            p.start()
        try:
            with pytest.raises(TailoringError) as exc_info:
                await run_tailoring_pipeline(pipeline_request)
        finally:
            for p in patchers:
                p.stop()

        assert exc_info.value.error_type == "FABRICATION_DETECTED"
