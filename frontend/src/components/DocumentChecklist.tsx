"use client";

import React from "react";

interface DocumentChecklistProps {
  missingDocuments: string[];
  onToggleDocument?: (documentName: string) => void;
}

export const DocumentChecklist: React.FC<DocumentChecklistProps> = ({
  missingDocuments,
  onToggleDocument,
}) => {
  const formatDocName = (name: string) => {
    return name
      .replace(/_/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  return (
    <div className="w-full bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3">
        <div>
          <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
            <span>📋 Dossier Missing Documents</span>
          </h3>
          <p className="text-xs text-slate-500">
            Audit checklist monitored by AI Application Guide
          </p>
        </div>

        <span
          className={`text-xs font-semibold px-3 py-1 rounded-full border ${
            missingDocuments.length > 0
              ? "bg-amber-50 text-amber-800 border-amber-200"
              : "bg-emerald-50 text-emerald-800 border-emerald-200"
          }`}
        >
          {missingDocuments.length > 0
            ? `${missingDocuments.length} Pending`
            : "Complete ✓"}
        </span>
      </div>

      {missingDocuments.length > 0 ? (
        <div className="space-y-2.5">
          {missingDocuments.map((doc, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-slate-800 transition-all hover:bg-amber-100/60"
            >
              <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-amber-200/80 text-amber-900 font-bold text-xs flex items-center justify-center shrink-0">
                  📄
                </div>
                <div>
                  <div className="font-bold text-xs text-slate-900">
                    {formatDocName(doc)}
                  </div>
                  <div className="text-[10px] text-amber-800">
                    Required for application verification
                  </div>
                </div>
              </div>

              {onToggleDocument && (
                <button
                  onClick={() => onToggleDocument(doc)}
                  className="px-3 py-1.5 rounded-lg bg-white border border-amber-300 text-amber-900 hover:bg-emerald-600 hover:text-white hover:border-emerald-600 font-semibold text-xs transition-all shadow-sm shrink-0"
                >
                  Mark Ready ✓
                </button>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="p-6 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-center space-y-2">
          <div className="text-2xl">🎉</div>
          <div className="font-extrabold text-sm">All Documents Ready!</div>
          <p className="text-xs text-emerald-700 max-w-sm mx-auto">
            Your application dossier has passed all document audit checks and is ready for final review and submission.
          </p>
        </div>
      )}
    </div>
  );
};
