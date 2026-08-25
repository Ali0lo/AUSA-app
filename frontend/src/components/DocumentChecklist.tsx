"use client";

import { Check, X } from "lucide-react";
import { formatDocumentName } from "@/lib/format";

interface DocumentChecklistProps {
  missingDocuments: string[];
  onToggleDocument?: (documentName: string) => void;
}

const standardDocuments = ["official_transcript", "passport_copy", "motivation_letter"];

export function DocumentChecklist({ missingDocuments, onToggleDocument }: DocumentChecklistProps) {
  const documents = Array.from(new Set([...standardDocuments, ...missingDocuments]));

  return (
    <section className="panel-strong p-6 sm:p-8" aria-labelledby="document-checklist-heading">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line pb-5">
        <div>
          <h2 id="document-checklist-heading" className="font-serif text-2xl font-semibold">Document checklist</h2>
          <p className="mt-1 text-sm text-muted">Changing an item updates this page only. The current backend does not save checklist changes.</p>
        </div>
        <span className={`status-tag ${missingDocuments.length ? "status-experimental" : "status-available"}`}>
          {missingDocuments.length ? `${missingDocuments.length} missing` : "All marked ready"}
        </span>
      </div>

      <ul className="mt-6 divide-y divide-quiet border-y border-quiet">
        {documents.map((document) => {
          const missing = missingDocuments.includes(document);
          return (
            <li key={document} className="flex flex-col gap-4 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <span className={`flex h-8 w-8 items-center justify-center border ${missing ? "border-danger text-danger" : "border-success bg-success text-paper"}`}>
                  {missing ? <X size={16} aria-label="Missing" /> : <Check size={16} aria-label="Ready" />}
                </span>
                <div>
                  <p className="font-semibold">{formatDocumentName(document)}</p>
                  <p className={`mt-1 text-xs ${missing ? "text-danger" : "text-success"}`}>{missing ? "Marked missing" : "Marked ready"}</p>
                </div>
              </div>
              {onToggleDocument && (
                <button type="button" className="button-quiet" onClick={() => onToggleDocument(document)}>
                  {missing ? "Mark ready" : "Mark missing"}
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
