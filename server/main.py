"""AI Resume Screener backend entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import settings
from server.routers import auth, explainability, ingest, notify, ranking, results, upload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="AI Resume Screener Backend",
    description=(
        "Resume and JD upload, NLP processing, ranking, notifications, and explainability APIs."
    ),
    version="1.1.0",
)

_allowed_origins = [
    origin.strip()
    for origin in settings.cors_origin.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"http://localhost(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(ranking.router)
app.include_router(ingest.router)
app.include_router(results.router)
app.include_router(notify.router)
app.include_router(explainability.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "ai-resume-screener-backend"}
