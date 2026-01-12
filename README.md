# TailorCV

> **Intelligent CV tailoring powered by AI** - Transform your resume to perfectly match any job description while maintaining complete factual integrity.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6.svg)](https://typescriptlang.org)
[![Material UI](https://img.shields.io/badge/MUI-7.3-007FFF.svg)](https://mui.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

TailorCV is an AI-powered CV customization system that intelligently adapts your resume for specific job positions. Unlike generic resume builders, TailorCV analyzes both your CV and the target job description to create a perfectly matched application.

### Core Philosophy

> **This system never fabricates experience** - it only reorganizes, reframes, and highlights existing facts from your original CV.

Every modification is traceable back to your original experience. The system includes built-in guardrails that detect and block any attempt to add unevidenced claims.

---

## Features

### Intelligent Analysis
- **Job Requirements Extraction** - Parses job descriptions to identify must-have requirements, nice-to-have qualifications, implied skills, and ATS keywords
- **CV Facts Extraction** - Preserves all verifiable facts from your original CV without interpretation or embellishment
- **Smart Mapping** - Creates explicit mappings between job requirements and your evidence with relevance scoring

### Tailored Output
- **Adaptive Rewriting** - Reframes achievements using job-relevant language while maintaining accuracy
- **Section Reorganization** - Prioritizes the most relevant experience for each role
- **Keyword Optimization** - Naturally integrates ATS-friendly keywords from the job posting
- **Cover Letter Generation** - Creates complementary cover letters tailored to both the job and your background

### Quality Assurance
- **Fabrication Detection** - Blocks any output containing companies, skills, or metrics not in your original CV
- **Borderline Flagging** - Identifies changes that may need your review before use
- **Match Scoring** - Provides detailed breakdown of how well you match each requirement
- **Change Logging** - Documents every modification with justifications

### Export Options
- **Multiple Formats** - Export as Markdown, Word (.docx), or PDF
- **Three Strictness Levels** - Conservative, Moderate, or Aggressive tailoring

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript 5.8, Material UI 7.3, Vite |
| **Backend** | Python 3.11+, FastAPI 0.109, Pydantic 2.5 |
| **AI Engine** | Google Gemini API (gemini-1.5-flash) |
| **Document Processing** | PyPDF2, python-docx, WeasyPrint |
| **Containerization** | Docker, Docker Compose |

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Option 1: Local Development

#### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/Mac

# Edit .env and add your GEMINI_API_KEY
notepad .env                 # Windows
# nano .env                  # Linux/Mac

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 2: Docker Deployment

```bash
# Set your API key (Windows)
set GEMINI_API_KEY=your_api_key_here

# Set your API key (Linux/Mac)
export GEMINI_API_KEY=your_api_key_here

# Build and run
docker-compose up --build
```

---

## Usage Guide

### Step 1: Input Job Description
Paste the complete job posting into the first text area. The system will extract:
- Required and preferred qualifications
- Key responsibilities
- ATS keywords and their priority
- Company culture signals

### Step 2: Upload Your CV
Either upload a file (PDF, DOCX, or TXT) or paste your CV text directly. The system extracts:
- Work experience with detailed achievements
- Skills (both explicit and inferred from experience)
- Education and certifications
- Projects and accomplishments

### Step 3: Configure Options

| Strictness Level | Inferred Skills | Reframing | Keyword Injection | Best For |
|-----------------|-----------------|-----------|-------------------|----------|
| **Conservative** | Not allowed | Minimal | Only if evidenced | Regulated industries |
| **Moderate** | Allowed | Balanced | Natural integration | Most applications |
| **Aggressive** | Allowed | Extensive | Maximum ATS optimization | High-volume applications |

### Step 4: Review Results
- **Tailored CV** - Your reorganized and reframed resume
- **Match Analysis** - Detailed scoring and gap analysis
- **Changes Log** - Every modification with justification
- **Borderline Items** - Changes requiring your review
- **Cover Letter** - Optional tailored cover letter

### Step 5: Export
Download your tailored CV in your preferred format:
- **Markdown** - For easy editing and version control
- **Word (.docx)** - For traditional applications
- **PDF** - For final submission

---

## Architecture

```
                                    +-------------------+
                                    |    Frontend       |
                                    |  React + MUI      |
                                    +--------+----------+
                                             |
                                             | HTTP/REST
                                             v
+-------------------+              +-------------------+              +-------------------+
|   Job Description |  -------->  |    FastAPI        |  -------->  |   Gemini API      |
|   + Original CV   |             |    Backend        |             |   (LLM Engine)    |
+-------------------+              +--------+----------+              +-------------------+
                                             |
                    +------------------------+------------------------+
                    |                        |                        |
                    v                        v                        v
          +-----------------+      +-----------------+      +-----------------+
          | Job Extractor   |      | CV Extractor    |      | Mapper          |
          | (Module 1)      |      | (Module 2)      |      | (Module 3)      |
          +-----------------+      +-----------------+      +-----------------+
                    |                        |                        |
                    +------------------------+------------------------+
                                             |
                    +------------------------+------------------------+
                    |                        |                        |
                    v                        v                        v
          +-----------------+      +-----------------+      +-----------------+
          | CV Generator    |      | QA Guardrails   |      | Cover Letter    |
          | (Module 4)      |      | (Module 5)      |      | (Module 6)      |
          +-----------------+      +-----------------+      +-----------------+
                                             |
                                             v
                                  +-------------------+
                                  |  Tailored Output  |
                                  |  + Cover Letter   |
                                  +-------------------+
```

### Processing Pipeline

1. **Job Requirements Extractor** - Parses job description into structured requirements, responsibilities, keywords, and culture signals
2. **CV Facts Extractor** - Extracts only verifiable facts from your CV, preserving original wording
3. **Requirements-to-Evidence Mapper** - Creates explicit mappings with match types (direct, transferable, partial, learning potential)
4. **CV Generator** - Produces tailored CV with reorganized sections and reframed achievements
5. **Quality Assurance** - Validates output integrity, blocks fabrication, flags borderline items
6. **Cover Letter Generator** - Creates complementary cover letter based on mapping results

---

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tailor` | Main tailoring endpoint (text input) |
| `POST` | `/api/tailor/upload` | Tailor with file upload support |
| `POST` | `/api/extract-job` | Extract job requirements only |
| `POST` | `/api/extract-cv` | Extract CV facts only |
| `POST` | `/api/export/{format}` | Export results (markdown/docx/pdf) |
| `POST` | `/api/set-api-key` | Set API key for session |
| `GET` | `/health` | Health check endpoint |

### Example Request

```bash
curl -X POST "http://localhost:8000/api/tailor" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Senior Software Engineer...",
    "cv_text": "John Doe\nSoftware Engineer with 5 years experience...",
    "options": {
      "strictness": "moderate",
      "include_cover_letter": true,
      "output_format": "markdown"
    }
  }'
```

Full API documentation available at `/docs` when running the backend.

---

## Project Structure

```
TailorCV/
├── backend/                          # Python FastAPI application
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Settings & configuration
│   │   ├── models/                  # Pydantic data models
│   │   │   ├── job_requirements.py  # Job requirement structures
│   │   │   ├── cv_facts.py          # CV parsing models
│   │   │   ├── mapping.py           # Requirement-to-evidence mapping
│   │   │   ├── options.py           # Tailoring options
│   │   │   └── output.py            # Tailored CV output models
│   │   ├── services/                # Core business logic
│   │   │   ├── job_extractor.py     # Module 1: Extract job requirements
│   │   │   ├── cv_extractor.py      # Module 2: Extract CV facts
│   │   │   ├── mapper.py            # Module 3: Map requirements to evidence
│   │   │   ├── cv_generator.py      # Module 4: Generate tailored CV
│   │   │   ├── qa_guardrails.py     # Module 5: Quality assurance
│   │   │   └── cover_letter.py      # Module 6: Generate cover letter
│   │   ├── utils/
│   │   │   ├── llm_client.py        # Gemini API wrapper
│   │   │   ├── document_parser.py   # PDF/DOCX/TXT parsing
│   │   │   └── exporters.py         # Export format generators
│   │   └── routers/
│   │       └── tailor.py            # API route definitions
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Backend container config
│   ├── .env.example                 # Environment template
│   └── .env                         # Local environment (git-ignored)
│
├── frontend/                         # React TypeScript application
│   ├── src/
│   │   ├── App.tsx                  # Main app with stepper workflow
│   │   ├── components/              # React components
│   │   │   ├── JobDescriptionInput.tsx
│   │   │   ├── CVUploader.tsx
│   │   │   ├── OptionsPanel.tsx
│   │   │   ├── ResultsDisplay.tsx
│   │   │   └── ExportOptions.tsx
│   │   ├── services/
│   │   │   └── api.ts               # Axios API client
│   │   └── types/
│   │       └── index.ts             # TypeScript definitions
│   ├── package.json                 # Dependencies & scripts
│   ├── vite.config.ts               # Vite build configuration
│   ├── tsconfig.json                # TypeScript configuration
│   └── Dockerfile                   # Frontend container config
│
├── docker-compose.yml               # Multi-container orchestration
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `DEBUG` | No | `false` | Enable debug mode |
| `GEMINI_MODEL` | No | `gemini-1.5-flash` | Gemini model to use |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Allowed CORS origins |

### Frontend Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000/api` | Backend API URL |

---

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Formatting

```bash
# Backend
cd backend
black .
isort .

# Frontend
cd frontend
npm run lint
npm run format
```

### Building for Production

```bash
# Frontend build
cd frontend
npm run build

# Docker production build
docker-compose -f docker-compose.prod.yml up --build
```

---

## Troubleshooting

### Common Issues

**API Key Error**
```
Error: Invalid API key
```
Ensure your `GEMINI_API_KEY` is correctly set in the backend `.env` file.

**CORS Error**
```
Access to fetch has been blocked by CORS policy
```
Add your frontend URL to `CORS_ORIGINS` in the backend configuration.

**Document Parsing Failed**
```
Error: Could not extract text from document
```
Ensure the uploaded file is a valid PDF, DOCX, or TXT file. Some PDFs with embedded images may not parse correctly.

**WeasyPrint PDF Export Issues (Windows)**
WeasyPrint requires GTK libraries. Install using:
```bash
pip install weasyprint
# May need additional system dependencies - see WeasyPrint docs
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) for the AI engine
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [Material UI](https://mui.com/) for the beautiful React components
- [WeasyPrint](https://weasyprint.org/) for PDF generation

---

<p align="center">
  Made with care for job seekers everywhere
</p>
