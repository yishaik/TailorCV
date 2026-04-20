"""
Tests for the shared tailoring pipeline.
"""
import pytest
from unittest.mock import AsyncMock, patch

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


def _patch_pipeline_services():
    """Patch all service functions used by the pipeline."""
    return (
        patch("app.services.tailoring_pipeline.extract_job_requirements", new_callable=AsyncMock),
        patch("app.services.tailoring_pipeline.extract_cv_facts", new_callable=AsyncMock),
        patch("app.services.tailoring_pipeline.map_requirements_to_evidence", new_callable=AsyncMock),
        patch("app.services.tailoring_pipeline.generate_tailored_cv", new_callable=AsyncMock),
        patch("app.services.tailoring_pipeline.run_quality_checks"),
        patch("app.services.tailoring_pipeline.generate_cover_letter", new_callable=AsyncMock),
    )


class TestTailoringPipeline:
    @pytest.mark.anyio
    async def test_successful_run(self, pipeline_request):
        with (
            _patch_pipeline_services()[0] as mock_extract_job,
            _patch_pipeline_services()[1] as mock_extract_cv,
            _patch_pipeline_services()[2] as mock_map,
            _patch_pipeline_services()[3] as mock_gen_cv,
            _patch_pipeline_services()[4] as mock_qa,
            _patch_pipeline_services()[5] as mock_cover,
        ):
            mock_extract_job.return_value = make_job_requirements()
            mock_extract_cv.return_value = make_cv_facts()
            mock_map.return_value = make_mapping()
            mock_gen_cv.return_value = (make_tailored_cv(), [], [])
            mock_qa.return_value = (True, [], [], make_match_score())
            mock_cover.return_value = None

            with patch("app.services.tailoring_pipeline.extract_job_requirements", new_callable=AsyncMock) as m1, \
                 patch("app.services.tailoring_pipeline.extract_cv_facts", new_callable=AsyncMock) as m2, \
                 patch("app.services.tailoring_pipeline.map_requirements_to_evidence", new_callable=AsyncMock) as m3, \
                 patch("app.services.tailoring_pipeline.generate_tailored_cv", new_callable=AsyncMock) as m4, \
                 patch("app.services.tailoring_pipeline.run_quality_checks") as m5, \
                 patch("app.services.tailoring_pipeline.generate_cover_letter", new_callable=AsyncMock) as m6:
                m1.return_value = make_job_requirements()
                m2.return_value = make_cv_facts()
                m3.return_value = make_mapping()
                m4.return_value = (make_tailored_cv(), [], [])
                m5.return_value = (True, [], [], make_match_score())
                m6.return_value = None

                result = await run_tailoring_pipeline(pipeline_request)

            assert result.tailored_cv.header.name == "Jane Doe"
            assert result.match_score.score == 75

    @pytest.mark.anyio
    async def test_progress_callback(self, pipeline_request):
        steps = []

        def on_step(step, total, msg):
            steps.append((step, total, msg))

        with patch("app.services.tailoring_pipeline.extract_job_requirements", new_callable=AsyncMock) as m1, \
             patch("app.services.tailoring_pipeline.extract_cv_facts", new_callable=AsyncMock) as m2, \
             patch("app.services.tailoring_pipeline.map_requirements_to_evidence", new_callable=AsyncMock) as m3, \
             patch("app.services.tailoring_pipeline.generate_tailored_cv", new_callable=AsyncMock) as m4, \
             patch("app.services.tailoring_pipeline.run_quality_checks") as m5:
            m1.return_value = make_job_requirements()
            m2.return_value = make_cv_facts()
            m3.return_value = make_mapping()
            m4.return_value = (make_tailored_cv(), [], [])
            m5.return_value = (True, [], [], make_match_score())

            await run_tailoring_pipeline(pipeline_request, on_step=on_step)

        # Should have 6 progress callbacks (no cover letter)
        assert len(steps) == 6
        assert steps[0][0] == 1  # step 1
        assert steps[-1][0] == 6  # step 6

    @pytest.mark.anyio
    async def test_fabrication_raises_error(self, pipeline_request):
        with patch("app.services.tailoring_pipeline.extract_job_requirements", new_callable=AsyncMock) as m1, \
             patch("app.services.tailoring_pipeline.extract_cv_facts", new_callable=AsyncMock) as m2, \
             patch("app.services.tailoring_pipeline.map_requirements_to_evidence", new_callable=AsyncMock) as m3, \
             patch("app.services.tailoring_pipeline.generate_tailored_cv", new_callable=AsyncMock) as m4, \
             patch("app.services.tailoring_pipeline.run_quality_checks") as m5:
            m1.return_value = make_job_requirements()
            m2.return_value = make_cv_facts()
            m3.return_value = make_mapping()
            m4.return_value = (make_tailored_cv(), [], [])
            m5.return_value = (False, ["Fabricated company"], [], make_match_score())

            with pytest.raises(TailoringError) as exc_info:
                await run_tailoring_pipeline(pipeline_request)

            assert exc_info.value.error_type == "FABRICATION_DETECTED"
