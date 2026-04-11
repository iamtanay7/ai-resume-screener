"""Upload a local document to GCS and run Tanay's NLP pipeline against it."""

from __future__ import annotations

import argparse
import json
import mimetypes
import uuid
from pathlib import Path

from services.nlp_pipeline import UploadEvent, build_embedding, parse_document, process_upload_event
from services.storage import upload_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload a local PDF/DOCX to GCS and test Document AI + Vertex embeddings.",
    )
    parser.add_argument(
        "--kind",
        required=True,
        choices=["resume_uploaded", "jd_uploaded"],
        help="Event type to simulate.",
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Local PDF or DOCX file to upload.",
    )
    parser.add_argument(
        "--document-id",
        help="Optional candidate ID or job ID. Defaults to a generated UUID.",
    )
    parser.add_argument(
        "--title",
        help="Optional title for JD events.",
    )
    parser.add_argument(
        "--email",
        help="Optional email for resume events.",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Run the full pipeline and persist parsed artifacts/embeddings to Firestore.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional path to write the parsed payload and embedding summary as JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    local_file = args.file.expanduser().resolve()

    if not local_file.exists():
        raise FileNotFoundError(f"File not found: {local_file}")

    extension = local_file.suffix.lower()
    if extension not in {".pdf", ".docx"}:
        raise ValueError("Only PDF and DOCX files are supported.")

    document_id = args.document_id or str(uuid.uuid4())
    destination_prefix = "resumes" if args.kind == "resume_uploaded" else "jds"
    destination_path = f"{destination_prefix}/{document_id}{extension}"
    content_type = mimetypes.guess_type(local_file.name)[0] or "application/octet-stream"

    file_bytes = local_file.read_bytes()
    gcs_path = upload_file(
        file_bytes=file_bytes,
        destination_path=destination_path,
        content_type=content_type,
    )

    event = UploadEvent(
        kind=args.kind,
        document_id=document_id,
        gcs_path=gcs_path,
        title=args.title,
        email=args.email,
    )

    if args.persist:
        process_upload_event(event)
        print(json.dumps({"documentId": document_id, "gcsPath": gcs_path, "persisted": True}, indent=2))
        return

    parsed = parse_document(event)
    embedding = build_embedding(parsed)
    payload = {
        "documentId": document_id,
        "gcsPath": gcs_path,
        "kind": parsed.kind,
        "metadata": parsed.metadata,
        "sectionTitles": [section.title for section in parsed.sections],
        "sectionCount": len(parsed.sections),
        "textPreview": parsed.extractedText[:1000],
        "embeddingModel": embedding.model,
        "embeddingDimension": len(embedding.vector),
    }

    if args.out:
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote output to {args.out}")
        return

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
