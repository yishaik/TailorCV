"""
FastAPI application entry point.
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .routers import tailor
from .utils.rate_limit import limiter, rate_limit_handler

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent CV tailoring system that customizes CVs for specific job descriptions",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tailor.router, prefix="/api", tags=["tailor"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/debug/pipeline-steps")
async def debug_pipeline_steps():
    """Debug endpoint — test each Gemini call individually."""
    import time
    import traceback
    from .services.job_extractor import extract_job_requirements
    from .services.cv_extractor import extract_cv_facts
    from .utils.llm_client import get_llm_client

    results = {}
    test_job = "We need a Python developer with 3 years experience building REST APIs."
    test_cv = "Jane Doe. Software Engineer at Acme Corp. Built REST APIs with Python. Skills: Python, FastAPI, Docker. Education: BSc CS MIT 2019."

    # Test 1: LLM client init
    t0 = time.time()
    try:
        client = get_llm_client()
        results["llm_client"] = {"status": "ok", "has_key": bool(client.api_key), "model": client.model_name, "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        results["llm_client"] = {"status": "error", "error": str(e)}

    # Test 2: Simple Gemini call
    t0 = time.time()
    try:
        resp = await asyncio.wait_for(client.generate_text("Say hello"), timeout=10)
        results["simple_call"] = {"status": "ok", "response": resp[:100], "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        results["simple_call"] = {"status": "error", "error": str(e), "trace": traceback.format_exc()[-300]}

    # Test 3: Extract job
    t0 = time.time()
    try:
        await asyncio.wait_for(extract_job_requirements(test_job), timeout=20)
        results["extract_job"] = {"status": "ok", "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        results["extract_job"] = {"status": "error", "error": str(e), "trace": traceback.format_exc()[-300]}

    # Test 4: Extract CV
    t0 = time.time()
    try:
        await asyncio.wait_for(extract_cv_facts(test_cv), timeout=25)
        results["extract_cv"] = {"status": "ok", "seconds": round(time.time() - t0, 1)}
    except asyncio.TimeoutError:
        results["extract_cv"] = {"status": "error", "error": "TIMEOUT after 25s"}
    except Exception as e:
        results["extract_cv"] = {
            "status": "error",
            "error": repr(e),
            "error_type": type(e).__name__,
            "trace": traceback.format_exc()[-500]
        }

    return results


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs_url": "/docs",
        "health_url": "/health"
    }
