"""
FastAPI application entry point.
"""
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
    """Debug endpoint — time each Gemini call in the pipeline."""
    import time
    from .services.job_extractor import extract_job_requirements
    from .services.cv_extractor import extract_cv_facts

    results = {}
    test_job = "We need a Python developer with 3 years experience building REST APIs."
    test_cv = "Jane Doe. Software Engineer at Acme Corp. Built REST APIs with Python."

    for name, fn, arg in [
        ("extract_job", extract_job_requirements, test_job),
        ("extract_cv", extract_cv_facts, test_cv),
    ]:
        t0 = time.time()
        try:
            await fn(arg)
            results[name] = {"status": "ok", "seconds": round(time.time() - t0, 1)}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e), "seconds": round(time.time() - t0, 1)}

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
