"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Converts a gs:// Cloud Storage URI to an HTTPS URL that browsers can fetch.
 * Works when the bucket has public (uniform) access. Falls back to showing the raw path.
 */
function gcsToHttpUrl(uri: string): string {
  if (!uri.startsWith("gs://")) return uri;
  const path = uri.slice("gs://".length);
  return `https://storage.googleapis.com/${path}`;
}

interface DocumentPreviewProps {
  /** Local File object (takes precedence over `src` when provided) */
  file?: File | null;
  /** Remote URL or gs:// path */
  src?: string;
  /** Label shown above the viewer */
  title?: string;
  /** Viewer height (Tailwind class, defaults to h-[500px]) */
  heightClass?: string;
}

export function DocumentPreview({ file, src, title, heightClass = "h-[500px]" }: DocumentPreviewProps) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Build a fresh object URL whenever the local file changes, clean up on unmount.
  useEffect(() => {
    if (!file) {
      setObjectUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setObjectUrl(url);
    setLoadError(false);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const resolvedSrc = objectUrl ?? (src ? gcsToHttpUrl(src) : null);
  const fileName = file?.name ?? (src ? src.split("/").pop() : "document");
  const isPdf =
    file?.type === "application/pdf" ||
    (file?.name ?? src ?? "").toLowerCase().endsWith(".pdf");

  return (
    <div className="space-y-2">
      {title && (
        <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
          {title}
        </p>
      )}

      <div
        className={`relative w-full rounded-xl border border-neutral-200 overflow-hidden bg-neutral-50 ${heightClass}`}
      >
        {resolvedSrc && isPdf && !loadError ? (
          <iframe
            ref={iframeRef}
            src={resolvedSrc}
            className="w-full h-full"
            title={fileName}
            onError={() => setLoadError(true)}
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
            <FileIcon />
            {loadError ? (
              <>
                <p className="text-sm font-medium text-neutral-600">
                  Could not load document
                </p>
                <p className="text-xs text-neutral-400 break-all max-w-sm">
                  {src ? `GCS path: ${src}` : fileName}
                </p>
                <p className="text-xs text-neutral-400">
                  The file may be stored in a private GCS bucket. Contact your admin for access.
                </p>
              </>
            ) : !resolvedSrc ? (
              <p className="text-sm text-neutral-400">No document available</p>
            ) : (
              <>
                <p className="text-sm font-medium text-neutral-600">
                  Preview not available for this file type
                </p>
                <p className="text-xs text-neutral-400">{fileName}</p>
              </>
            )}
          </div>
        )}
      </div>

      {/* File info bar */}
      {(file || src) && (
        <div className="flex items-center justify-between text-xs text-neutral-400">
          <span className="truncate max-w-[260px]">{fileName}</span>
          {file && (
            <span className="shrink-0 ml-2">
              {file.size < 1024 * 1024
                ? `${(file.size / 1024).toFixed(0)} KB`
                : `${(file.size / (1024 * 1024)).toFixed(1)} MB`}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

function FileIcon() {
  return (
    <svg
      className="h-10 w-10 text-neutral-300"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
      />
    </svg>
  );
}
