# AI Resume Screener

AI Resume Screener is a web application that helps recruiters evaluate candidate resumes against job descriptions using document parsing, semantic matching, ranking, and explainable outcomes.

## Objective

Build an end-to-end system that can:

- accept recruiter and candidate uploads,
- extract structured resume/JD information,
- compute candidate-job fit,
- rank candidates with transparent scoring,
- support recruiter decisions with clear explanations.

## High-Level Architecture

Frontend -> Cloud Run API -> Cloud Storage -> Document AI -> Vertex AI Embeddings -> Vertex AI Vector Search -> Matching + Ranking Engine -> Explainability Service -> Recruiter Results + Notifications

### Platform Components

- **Cloud Run**: hosts backend APIs and processing services.
- **Cloud Storage**: stores raw uploaded files and optional processed artifacts.
- **Document AI**: extracts plain text and structured sections from resumes/JDs.
- **Vertex AI Embeddings**: generates semantic vectors for resume/JD content.
- **Vertex AI Vector Search**: retrieves semantically similar content.
- **Firestore**: stores metadata, statuses, score outputs, and decision artifacts.
- **Pub/Sub / Storage Events**: triggers asynchronous processing pipelines.

## MVP Definition

- One job description evaluated against multiple candidate resumes.
- Score output includes weighted breakdown (not just yes/no).
- Final decision states:
  - `shortlist`
  - `manual_review`
  - `reject`
- Recruiter-facing ranked result view.
- Candidate notifications sent only after recruiter approval.

## Team Ownership

- **Raj**: Frontend + Upload Service
- **Asmita**: Data Ingestion + Storage
- **Tanay**: NLP Processing (Document AI + Embeddings)
- **Michael**: Matching + Ranking Engine
- **Adwait**: Explainability + Dashboard

## Workflow Phases

1. Define scope and scoring criteria.
2. Set up required Google Cloud services.
3. Build upload APIs and frontend upload flows.
4. Implement document ingestion/parsing pipeline.
5. Add semantic matching with embeddings + vector search.
6. Add ranking layer with hard filters and weighted scoring.
7. Generate structured explanations.
8. Build recruiter results and notification workflow.
9. Add logging, monitoring, and failure tracking.
10. Validate with realistic resume/JD test scenarios.

## Match Criteria (Project-Level)

- Skills fit
- Experience fit
- Education fit
- Keywords/certifications
- Optional location/work authorization constraints

## Target Demo Flow

1. Recruiter uploads a JD.
2. Candidates upload resumes.
3. Files are stored in Cloud Storage.
4. Document AI extracts structured content.
5. Embeddings are generated in Vertex AI.
6. Vector Search retrieves semantic matches.
7. Ranking engine computes weighted scores and outcomes.
8. Explainability service generates decision rationale.
9. Recruiter sees ranked candidates with score breakdown.

## Reliability Expectations

- Log each stage: upload, parse, embedding, vector query, ranking, final outcome.
- Track failure causes: unreadable files, parsing issues, missing critical fields, empty JD.
- Persist timestamps and processing status in Firestore.
- Validate behavior on exact match, partial match, mismatch, missing required skills, and unreadable inputs.

## Current Repository Status

This repository is currently in initial bootstrap stage and starts with project-level documentation before team-owned components are implemented.

## Stack

- **Frontend** — Next.js 14, TypeScript, Tailwind CSS
- **Backend** — FastAPI, Python
- **AI/ML** — Vertex AI, Gemini (embedding + explanation)
- **Infra** — Google Cloud Storage, Firestore, Pub/Sub

## Pipeline

Upload → Parse → Embed → Match → Rank → Explain

## Getting Started

### Client

```bash
cd client
npm install
npm run dev
```

Runs at `http://localhost:3000`

### Server

```bash
pip install -r server/requirements.txt
uvicorn server.main:app --reload
```

Runs at `http://localhost:8000`

### Server Docker image

Build from the repository root:

```bash
docker build -f server/Dockerfile . -t ai-resume-screener-server
docker run -p 8080:8080 ai-resume-screener-server
```

This Dockerfile assumes the repo-root build context so `server/requirements.txt` and the `server/` package are available at build time.

### Visual Ranking Demo

```bash
python -m server.tests.demo_ranking_visual
```

This generates `server/tests/_ranking_demo.html` and opens it in your browser.

## Usage

- **Recruiter** — upload a job description, get ranked candidates with match scores and AI explanations
- **Candidate** — upload a resume, get matched against open roles
