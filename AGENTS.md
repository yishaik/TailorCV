# Repository Guidelines

## Project Structure & Module Organization
- `backend/` contains the FastAPI service. Core logic is under `backend/app/services/`, with models in `backend/app/models/` and routes in `backend/app/routers/`.
- `frontend/` contains the React + TypeScript UI. Components live in `frontend/src/components/`, API calls in `frontend/src/services/`, and shared types in `frontend/src/types/`.
- Root files: `docker-compose.yml` for multi-service runs and `README.md` for architecture and setup details.

## Build, Test, and Development Commands
- Backend (from `backend/`):
  - `python -m venv venv` and `venv\Scripts\activate` to set up the venv.
  - `pip install -r requirements.txt` to install dependencies.
  - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` to run the API.
- Frontend (from `frontend/`):
  - `npm install` to install dependencies.
  - `npm run dev` to start the Vite dev server.
  - `npm run build` to build for production.
  - `npm run lint` to run ESLint.
- Docker: `docker-compose up --build` to run both services together.

## Coding Style & Naming Conventions
- Python modules use `snake_case` file names and `PascalCase` classes (Pydantic models).
- React components use `PascalCase` file names; variables and hooks use `camelCase`.
- Indentation is 4 spaces in Python and 2 spaces in TypeScript/JSON.
- ESLint is configured in `frontend/eslint.config.js`; no formatter is enforced, so follow existing style.

## Testing Guidelines
- No automated tests are currently configured.
- If you add tests, keep Python tests in `backend/tests/` and frontend tests in `frontend/src/__tests__/`, and update `README.md` with the runner commands.

## Commit & Pull Request Guidelines
- Use concise, imperative commit messages (e.g., `Add SSE progress handling`).
- PRs should include: a clear summary, steps to run locally, and screenshots/GIFs for UI changes.
- Link related issues and call out any new config or env vars.

## Configuration & Secrets
- Backend config is loaded from `backend/.env` (copy from `backend/.env.example`). Never commit real API keys.
- Frontend API base URL is `VITE_API_URL` (defaults to `http://localhost:8000/api`).
