# Repository Guidelines

## Project Structure & Module Organization
- `backend/` houses the FastAPI service. Core modules live in `backend/app/` with `models/`, `services/`, `routers/`, and `utils/`.
- `frontend/` is the React + TypeScript client. UI lives in `frontend/src/`, with API wiring in `frontend/src/services/`.
- Root-level files include `docker-compose.yml` for local orchestration and `README.md` for full setup details.

## Build, Test, and Development Commands
- Backend dev server: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (run from `backend/`).
- Frontend dev server: `npm run dev` (run from `frontend/`).
- Frontend production build: `npm run build`.
- Frontend linting: `npm run lint`.
- Docker: `docker-compose up --build` for a full-stack local run.

## Coding Style & Naming Conventions
- Python follows standard PEP 8 conventions; keep module names snake_case and classes in PascalCase.
- TypeScript follows ESLint defaults from `frontend/eslint.config.js`; prefer `PascalCase` for components and `camelCase` for hooks, props, and functions.
- Indentation is 4 spaces for Python and 2 spaces for TypeScript/JSON.

## Testing Guidelines
- No automated test runner is configured in the current repo (no `pytest` dependency or `npm test` script).
- If you add tests, keep Python tests under `backend/tests/` and frontend tests under `frontend/src/__tests__/`, and document the chosen runner in this file.

## Commit & Pull Request Guidelines
- Git history currently shows a single commit message in the form `Initial commit: ...`, so no strict convention is established.
- Use clear, imperative summaries (e.g., `Add CV mapping guardrails`) and include context in the PR description.
- For PRs, include: a short overview, any linked issues, and screenshots/GIFs for UI changes.

## Configuration & Secrets
- Backend config lives in `backend/.env` (see `backend/.env.example`); never commit real API keys.
- Frontend points to the API via `VITE_API_URL` (defaults to `http://localhost:8000/api`).
