---
name: tailorcv-portfolio-project
description: TailorCV is a portfolio piece the user wants production-ready to showcase in job applications
metadata:
  type: project
---

TailorCV (D:\Projects\TailorCV) is an AI CV-tailoring app (FastAPI + React/Vite, Google Gemini) that the user is polishing as a **portfolio piece to show prospective employers**. Production quality, clean README, green CI, and full-stack tests matter here — it's meant to impress in interviews.

**Why:** The user said they want to "brag about it when trying to get a job."

**How to apply:** Favor correctness, accurate docs, and passing CI over speed. Verify the actual toolchains (`pytest` in backend/, `npm test`/`npm run build` in frontend/) before claiming done.

History note (2026-06-13): local had ~3000 lines of uncommitted parallel work while origin/master was 27 commits ahead with an overlapping refactor. Reconciled as "remote wins, port local extras": the discarded local work is preserved on branch `backup/local-uncommitted-20260613` (recoverable). Fixed an app-breaking import (mapper needed helpers deleted from cv_extractor), removed a leaky `/debug` endpoint, and ported a Vitest frontend suite.
