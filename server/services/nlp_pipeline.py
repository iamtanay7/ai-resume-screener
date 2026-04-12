"""Starter NLP pipeline for Tanay's Document AI + embeddings work."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import vertexai
from google.api_core.client_options import ClientOptions
from google.cloud import documentai
from server.config import settings
from server.models.schemas import DocumentSection, EmbeddingRecord, ParsedDocument
from server.services import firestore_db, ranking_engine, storage
from vertexai.language_models import TextEmbeddingModel

logger = logging.getLogger(__name__)

SECTION_ALIASES = {
    "summary": {"summary", "professional summary", "profile", "objective"},
    "skills": {"skills", "technical skills", "core skills", "technologies", "competencies"},
    "experience": {"experience", "work experience", "professional experience", "employment"},
    "education": {"education", "academic background", "academics"},
    "projects": {"projects", "project experience"},
    "certifications": {"certifications", "certificates", "licenses"},
}

_documentai_client: documentai.DocumentProcessorServiceClient | None = None
_embedding_model: TextEmbeddingModel | None = None
_vertex_initialized = False


@dataclass
class UploadEvent:
    """Normalized event payload published from the upload service."""

    kind: str
    document_id: str
    gcs_path: str
    title: str | None = None
    email: str | None = None


def process_upload_event(event: UploadEvent) -> None:
    """
    Orchestrate Tanay's processing phase.

    Current behavior:
    - marks Firestore status through parse/embed stages
    - stores starter artifacts for parsed output and embedding output

    Replace the placeholder implementations below with:
    - Document AI parsing
    - section extraction / chunking
    - Vertex AI embedding generation
    """
    collection = _parent_collection(event.kind)
    _mark_status(event, "parsing")

    try:
        parsed = parse_document(event)
        firestore_db.save_nlp_artifact(
            parent_collection=collection,
            document_id=event.document_id,
            artifact_id="parsed",
            payload=parsed.model_dump(),
        )
        _mark_status(event, "parsed")

        embedding = build_embedding(parsed)
        _mark_status(event, "embedding")
        firestore_db.save_nlp_artifact(
            parent_collection=collection,
            document_id=event.document_id,
            artifact_id="embedding",
            payload=embedding.model_dump(),
        )
        _mark_status(event, "processed")
        _trigger_ranking(event)
    except Exception as exc:
        logger.exception("NLP pipeline failed for %s %s", event.kind, event.document_id)
        _mark_status(event, "failed", error=str(exc))
        raise


def parse_document(event: UploadEvent) -> ParsedDocument:
    """
    Parse a resume or JD with Document AI and normalize the extracted text.
    """
    kind = "resume" if event.kind == "resume_uploaded" else "job_description"
    file_bytes = storage.download_file(event.gcs_path)
    mime_type = _guess_mime_type(event.gcs_path)

    client = _get_documentai_client()
    request = documentai.ProcessRequest(
        name=_processor_name(_processor_id_for_event(event)),
        raw_document=documentai.RawDocument(
            content=file_bytes,
            mime_type=mime_type,
        ),
    )
    result = client.process_document(request=request)
    document = result.document
    extracted_text = (document.text or "").strip()

    if not extracted_text:
        raise ValueError(f"Document AI returned no text for {event.gcs_path}.")

    sections = _extract_sections(extracted_text)
    return ParsedDocument(
        documentId=event.document_id,
        kind=kind,
        sourceUrl=event.gcs_path,
        extractedText=extracted_text,
        sections=sections,
        metadata={
            "documentAiLocation": settings.document_ai_location,
            "processorId": _processor_id_for_event(event),
            "pageCount": str(len(document.pages)),
            "mimeType": mime_type,
        },
    )


def build_embedding(parsed: ParsedDocument) -> EmbeddingRecord:
    """
    Generate an embedding for the most useful combined document text.
    """
    text_for_embedding = _embedding_text(parsed)
    model = _get_embedding_model()
    embedding = model.get_embeddings([text_for_embedding])[0]
    return EmbeddingRecord(
        model=settings.vertex_embedding_model,
        vector=list(embedding.values),
        textSnippet=text_for_embedding[:500],
    )


def _processor_id_for_event(event: UploadEvent) -> str:
    if event.kind == "resume_uploaded":
        return settings.document_ai_resume_processor_id
    return settings.document_ai_jd_processor_id


def _parent_collection(event_kind: str) -> str:
    if event_kind == "resume_uploaded":
        return firestore_db.COLLECTION_CANDIDATES
    return firestore_db.COLLECTION_JOBS


def _mark_status(event: UploadEvent, status: str, error: str | None = None) -> None:
    if event.kind == "resume_uploaded":
        firestore_db.mark_candidate_processing(event.document_id, status, error=error)
        return
    firestore_db.mark_job_processing(event.document_id, status, error=error)


def _get_documentai_client() -> documentai.DocumentProcessorServiceClient:
    global _documentai_client
    if _documentai_client is None:
        _documentai_client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(
                api_endpoint=f"{settings.document_ai_location}-documentai.googleapis.com",
            )
        )
    return _documentai_client


def _processor_name(processor_id: str) -> str:
    return (
        f"projects/{settings.gcp_project_id}/locations/"
        f"{settings.document_ai_location}/processors/{processor_id}"
    )


def _get_embedding_model() -> TextEmbeddingModel:
    global _embedding_model, _vertex_initialized
    if not _vertex_initialized:
        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_region)
        _vertex_initialized = True

    if _embedding_model is None:
        _embedding_model = TextEmbeddingModel.from_pretrained(settings.vertex_embedding_model)
    return _embedding_model


def _guess_mime_type(gcs_path: str) -> str:
    normalized = gcs_path.lower()
    if normalized.endswith(".pdf"):
        return "application/pdf"
    if normalized.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    raise ValueError(f"Unsupported file type for '{gcs_path}'.")


def _extract_sections(extracted_text: str) -> list[DocumentSection]:
    normalized_lines = [line.strip() for line in extracted_text.splitlines()]
    lines = [line for line in normalized_lines if line]

    sections: list[DocumentSection] = []
    current_title = "full_text"
    current_lines: list[str] = []

    for line in lines:
        heading = _normalize_heading(line)
        if heading:
            if current_lines:
                sections.append(
                    DocumentSection(
                        title=current_title,
                        content="\n".join(current_lines).strip(),
                    )
                )
            current_title = heading
            current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        sections.append(
            DocumentSection(
                title=current_title,
                content="\n".join(current_lines).strip(),
            )
        )

    if not sections:
        sections.append(DocumentSection(title="full_text", content=extracted_text))

    return sections


def _normalize_heading(line: str) -> str | None:
    cleaned = re.sub(r"[^a-zA-Z ]+", " ", line).strip().lower()
    if not cleaned:
        return None

    for canonical_title, aliases in SECTION_ALIASES.items():
        if cleaned in aliases:
            return canonical_title
    return None


def _embedding_text(parsed: ParsedDocument) -> str:
    prioritized_titles = ["summary", "skills", "experience", "education", "projects", "certifications"]
    prioritized_chunks: list[str] = []

    for title in prioritized_titles:
        for section in parsed.sections:
            if section.title == title and section.content:
                prioritized_chunks.append(f"{title.upper()}\n{section.content}")

    if prioritized_chunks:
        return "\n\n".join(prioritized_chunks)

    return parsed.extractedText


def _trigger_ranking(event: UploadEvent) -> None:
    """
    Kick ranking after NLP completes.

    - When a JD finishes, rerank that job against all processed candidates.
    - When a resume finishes, rerank all jobs so the new candidate can appear in results.
    """
    if event.kind == "jd_uploaded":
        ranked_count = ranking_engine.run_ranking(job_id=event.document_id)
        logger.info("Triggered ranking for job %s. Candidates ranked=%s", event.document_id, ranked_count)
        return

    for job_id in firestore_db.list_job_ids():
        ranked_count = ranking_engine.run_ranking(job_id=job_id)
        logger.info(
            "Triggered ranking after candidate %s for job %s. Candidates ranked=%s",
            event.document_id,
            job_id,
            ranked_count,
        )
