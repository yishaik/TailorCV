"""
Tests for the FastAPI application.

Uses httpx.AsyncClient with the ASGI app for fast, in-process testing.
All LLM calls are mocked so no API key is needed.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.output import TailorResult
from app.services.tailoring_pipeline import TailoringError

from tests.conftest import (
    make_cv_facts,
    make_mapping,
    make_tailored_cv,
    make_match_score,
    make_tailor_request,
    JOB_DESCRIPTION,
    CV_TEXT,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _make_tailor_result() -> TailorResult:
    """Build a valid TailorResult for mocking."""
    return TailorResult(
        tailored_cv=make_tailored_cv(),
        cover_letter=None,
        changes_log=[],
        borderline_items=[],
        match_score=make_match_score(),
        mapping_summary={"overall_score": 75},
    )


# ===================================================================
# Health & root
# ===================================================================

class TestHealthEndpoints:
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_root(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data


# ===================================================================
# Tailor endpoint (non-streaming)
# ===================================================================

class TestTailorEndpoint:
    async def test_success(self, client):
        with patch("app.routers.tailor.run_tailoring_pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.return_value = _make_tailor_result()
            resp = await client.post("/api/tailor", json={
                "job_description": JOB_DESCRIPTION,
                "original_cv": CV_TEXT,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["tailored_cv"]["header"]["name"] == "Jane Doe"
        assert data["match_score"]["score"] == 75

    async def test_fabrication_returns_400(self, client):
        with patch("app.routers.tailor.run_tailoring_pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.side_effect = TailoringError(
                "FABRICATION_DETECTED", "Fake company", ["Company X not found"]
            )
            resp = await client.post("/api/tailor", json={
                "job_description": JOB_DESCRIPTION,
                "original_cv": CV_TEXT,
            })
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"] == "FABRICATION_DETECTED"

    async def test_validation_short_job_description(self, client):
        resp = await client.post("/api/tailor", json={
            "job_description": "too short",
            "original_cv": CV_TEXT,
        })
        assert resp.status_code == 422

    async def test_validation_short_cv(self, client):
        resp = await client.post("/api/tailor", json={
            "job_description": JOB_DESCRIPTION,
            "original_cv": "short",
        })
        assert resp.status_code == 422


# ===================================================================
# Tailor streaming endpoint
# ===================================================================

class TestTailorStreamEndpoint:
    async def test_stream_success(self, client):
        with patch("app.routers.tailor.run_tailoring_pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.return_value = _make_tailor_result()
            resp = await client.post("/api/tailor/stream", json={
                "job_description": JOB_DESCRIPTION,
                "original_cv": CV_TEXT,
            })
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        # Parse SSE events
        lines = resp.text.strip().split("\n")
        data_lines = [l for l in lines if l.startswith("data: ")]
        assert len(data_lines) >= 1
        last_event = json.loads(data_lines[-1].replace("data: ", ""))
        assert last_event["complete"] is True

    async def test_stream_fabrication_error(self, client):
        with patch("app.routers.tailor.run_tailoring_pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.side_effect = TailoringError("FABRICATION_DETECTED", "Bad", ["detail"])
            resp = await client.post("/api/tailor/stream", json={
                "job_description": JOB_DESCRIPTION,
                "original_cv": CV_TEXT,
            })
        data_lines = [l for l in resp.text.split("\n") if l.startswith("data: ")]
        last = json.loads(data_lines[-1].replace("data: ", ""))
        assert last["error"] is True


# ===================================================================
# File upload endpoints
# ===================================================================

class TestUploadEndpoints:
    async def test_invalid_file_type(self, client):
        resp = await client.post(
            "/api/tailor/upload",
            data={"job_description": JOB_DESCRIPTION},
            files={"cv_file": ("resume.exe", b"fake content", "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"] == "INVALID_FILE_TYPE"

    async def test_upload_stream_invalid_file(self, client):
        resp = await client.post(
            "/api/tailor/upload/stream",
            data={"job_description": JOB_DESCRIPTION},
            files={"cv_file": ("resume.exe", b"fake", "application/octet-stream")},
        )
        assert resp.status_code == 400


# ===================================================================
# Extract endpoints
# ===================================================================

class TestExtractEndpoints:
    async def test_extract_job_success(self, client):
        with patch("app.routers.tailor.extract_job_requirements", new_callable=AsyncMock) as mock:
            mock.return_value = make_job_requirements()
            resp = await client.post("/api/extract-job", json={
                "job_description": JOB_DESCRIPTION,
            })
        assert resp.status_code == 200
        assert resp.json()["job_title"] == "Senior Python Developer"

    async def test_extract_cv_success(self, client):
        mock_facts = make_cv_facts()
        with patch("app.routers.tailor.extract_cv_facts", new_callable=AsyncMock) as mock:
            mock.return_value = mock_facts
            resp = await client.post("/api/extract-cv", json={
                "cv_text": CV_TEXT,
            })
        assert resp.status_code == 200
        assert resp.json()["personal_info"]["name"] == "Jane Doe"


# ===================================================================
# Export endpoint
# ===================================================================

class TestExportEndpoint:
    async def test_export_markdown(self, client):
        result = _make_tailor_result()
        resp = await client.post(
            "/api/export/markdown",
            json=result.model_dump(),
        )
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]

    async def test_export_invalid_format(self, client):
        result = _make_tailor_result()
        resp = await client.post(
            "/api/export/xml",
            json=result.model_dump(),
        )
        assert resp.status_code == 400


# ===================================================================
# Rate limiting (smoke test)
# ===================================================================

class TestRateLimiting:
    async def test_rate_limit_returns_429_after_many_requests(self, client):
        """After many rapid requests, we should eventually get a 429."""
        with patch("app.routers.tailor.run_tailoring_pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.return_value = _make_tailor_result()
            status_codes = []
            for _ in range(15):
                resp = await client.post("/api/tailor", json={
                    "job_description": JOB_DESCRIPTION,
                    "original_cv": CV_TEXT,
                })
                status_codes.append(resp.status_code)
        # At least one should be rate limited
        assert 429 in status_codes, f"Expected at least one 429, got: {status_codes}"
