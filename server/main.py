"""
AI Resume Screener — Upload Service
Raj's Cloud Run backend: receive → validate → GCS → Firestore → Pub/Sub
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import settings
from server.routers import notify, ranking, results, upload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="AI Resume Screener — Upload Service",
    description=(
        "Entry point for resume and JD uploads. "
        "Validates files, stores them in Cloud Storage, "
        "writes metadata to Firestore, and fires Pub/Sub events."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(ranking.router)
app.include_router(results.router)
app.include_router(notify.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "upload-service"}
