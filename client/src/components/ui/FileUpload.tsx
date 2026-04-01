"use client";

import React, { useCallback, useRef, useState } from "react";

interface FileUploadProps {
  label: string;
  accept?: string;
  onFile: (file: File) => void;
  hint?: string;
}

export function FileUpload({
  label,
  accept = ".pdf,.docx",
  onFile,
  hint = "PDF or DOCX up to 10 MB",
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [selected, setSelected] = useState<File | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      setSelected(file);
      onFile(file);
    },
    [onFile]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="space-y-1.5">
      <p className="text-sm font-medium text-neutral-700">{label}</p>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={[
          "flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-10",
          "cursor-pointer transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary-400",
          dragging
            ? "border-primary-400 bg-primary-50"
            : selected
            ? "border-success-400 bg-success-50"
            : "border-neutral-300 bg-neutral-50 hover:border-primary-300 hover:bg-primary-50",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={onInputChange}
        />

        {selected ? (
          <>
            <DocumentCheckIcon />
            <div className="text-center">
              <p className="text-sm font-medium text-success-700">
                {selected.name}
              </p>
              <p className="text-xs text-neutral-500">
                {(selected.size / 1024 / 1024).toFixed(2)} MB — click to replace
              </p>
            </div>
          </>
        ) : (
          <>
            <UploadIcon />
            <div className="text-center">
              <p className="text-sm font-medium text-neutral-700">
                Drop file here or{" "}
                <span className="text-primary-600 underline">browse</span>
              </p>
              <p className="mt-0.5 text-xs text-neutral-400">{hint}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function UploadIcon() {
  return (
    <svg
      className="h-10 w-10 text-neutral-400"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
      />
    </svg>
  );
}

function DocumentCheckIcon() {
  return (
    <svg
      className="h-10 w-10 text-success-500"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}
