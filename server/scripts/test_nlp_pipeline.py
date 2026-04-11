"""Run Tanay's parse + embed pipeline against a real GCS document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.nlp_pipeline import UploadEvent, build_embedding, parse_document, process_upload_event


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test Document AI parsing and Vertex embeddings with a real gs:// file.",
    )
    parser.add_argument(
        "--kind",
        required=True,
        choices=["resume_uploaded", "jd_uploaded"],
        help="Event type to simulate.",
    )
    parser.add_argument(
        "--document-id",
        required=True,
        help="Candidate ID or job ID to associate with this test run.",
    )
    parser.add_argument(
        "--gcs-path",
        required=True,
        help="Full gs:// path to the uploaded PDF or DOCX.",
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
    event = UploadEvent(
        kind=args.kind,
        document_id=args.document_id,
        gcs_path=args.gcs_path,
        title=args.title,
        email=args.email,
    )

    if args.persist:
        process_upload_event(event)
        print("Persisted parsed output and embedding to Firestore.")
        return

    parsed = parse_document(event)
    embedding = build_embedding(parsed)

    payload = {
        "documentId": parsed.documentId,
        "kind": parsed.kind,
        "sourceUrl": parsed.sourceUrl,
        "metadata": parsed.metadata,
        "sectionTitles": [section.title for section in parsed.sections],
        "sectionCount": len(parsed.sections),
        "textPreview": parsed.extractedText[:1000],
        "embeddingModel": embedding.model,
        "embeddingDimension": len(embedding.vector),
        "embeddingSnippet": embedding.textSnippet,
    }

    if args.out:
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote output to {args.out}")
        return

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
