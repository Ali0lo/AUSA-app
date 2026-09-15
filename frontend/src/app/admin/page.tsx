"use client";
import { CatalogueReview } from "@/components/CatalogueReview";

import { CheckCircle2, Edit3, ExternalLink, RefreshCw } from "lucide-react";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { FeatureTag } from "@/components/FeatureTag";
import { Notice } from "@/components/Notice";
import { ServiceStatus } from "@/components/ServiceStatus";
import { fetchFlaggedPrograms, getUserFacingError, UserFacingError, verifyAndApproveProgram } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { FlaggedProgram, VerifyProgramPayload } from "@/types";

export default function AdminPage() {
  const { data: session } = useSession();
  const [programs, setPrograms] = useState<FlaggedProgram[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<UserFacingError | null>(null);
  const [editingProgram, setEditingProgram] = useState<FlaggedProgram | null>(null);
  const [editForm, setEditForm] = useState<VerifyProgramPayload>({});
  const [isVerifying, setIsVerifying] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const token = session?.user?.accessToken;

  async function loadData() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchFlaggedPrograms(token);
      setPrograms(data);
    } catch (err) {
      setError(getUserFacingError(err, "Admin flagged programs curation"));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    fetchFlaggedPrograms(token).then((data) => {
      if (active) { setPrograms(data); setError(null); }
    }).catch((err) => {
      if (active) { setPrograms([]); setError(getUserFacingError(err, "Admin flagged programs curation")); }
    }).finally(() => { if (active) setIsLoading(false); });
    return () => { active = false; };
  }, [token]);

  function openEditModal(program: FlaggedProgram) {
    setEditingProgram(program);
    setEditForm({
      university_name: program.university_name,
      program_name: program.program_name,
      degree_level: program.degree_level || "master",
      field: program.field || "",
      country: program.country || "",
      min_gpa: program.min_gpa ?? undefined,
      min_ielts: program.min_ielts ?? undefined,
      tuition_fee: program.tuition_fee ?? undefined,
      currency: program.currency || undefined,
      dim_score_required: program.dim_score_required ?? undefined,
      requires_studienkolleg: program.requires_studienkolleg ?? false,
    });
    setSuccessMessage(null);
  }

  async function handleApproveAndPublish(programId: number, payload?: VerifyProgramPayload) {
    setIsVerifying(true);
    setSuccessMessage(null);
    try {
      const dataToSubmit = payload || editForm;
      const res = await verifyAndApproveProgram(programId, dataToSubmit, token);
      
      setPrograms((current) => current.filter((p) => p.id !== programId));
      setEditingProgram(null);
      setSuccessMessage(res.message || `Program #${programId} verified and published.`);
    } catch (err) {
      setError(getUserFacingError(err, "Program verification"));
    } finally {
      setIsVerifying(false);
    }
  }

  return (
    <div className="app-page">
      <div className="flex flex-col gap-6 border-b border-line pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-3">
            <p className="eyebrow">Admin Data Curation</p>
            <FeatureTag state="available" label="Internal Curation" />
          </div>
          <h1 className="page-heading mt-4">Review and verify low-confidence scraped programs.</h1>
          <p className="body-large mt-5">
            Automated ingestion scripts flag any scraped record with a confidence score under 85%. Source review records who checked the data and when.
          </p>
        </div>
        <ServiceStatus />
      </div>

      <div className="mt-7 flex flex-wrap items-center justify-between gap-4">
        <Notice title="Human Verification Guardrail Enabled" tone="warning">
          Admission catalogue rows show their review status. Approve only facts you have checked against the cited sources.
        </Notice>
        <button
          type="button"
          className="button-quiet"
          onClick={() => void loadData()}
          disabled={isLoading}
        >
          <RefreshCw size={16} aria-hidden="true" />
          {isLoading ? "Refreshing" : "Refresh queue"}
        </button>
      </div>

      <CatalogueReview token={token} />

      {successMessage && (
        <div className="mt-6 flex items-center gap-3 border border-success bg-[#f2f9f4] p-4 text-sm font-semibold text-success" role="status">
          <CheckCircle2 size={18} />
          <span>{successMessage}</span>
        </div>
      )}

      {error && (
        <div className="mt-6 border border-danger bg-paper p-5" role="alert">
          <p className="font-semibold text-danger">{error.title}</p>
          <p className="mt-2 text-sm leading-6 text-muted">{error.message}</p>
        </div>
      )}

      <div className="mt-8 panel-strong overflow-hidden p-0">
        <div className="flex items-center justify-between border-b border-line p-5">
          <h2 className="font-serif text-xl font-semibold">Flagged Programs Queue ({programs.length})</h2>
          <span className="text-xs font-semibold uppercase tracking-wider text-muted">Verification Status: Flagged for Review</span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-sm font-semibold text-muted">
            Loading flagged programs from backend...
          </div>
        ) : programs.length === 0 ? (
          <div className="p-10 text-center">
            <CheckCircle2 size={36} className="mx-auto text-success" />
            <h3 className="mt-3 font-serif text-xl font-semibold">No Pending Flagged Programs</h3>
            <p className="mt-2 text-sm text-muted">All scraped program records have been verified or pass the 85% confidence threshold.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line bg-[#f8f5ef] text-xs font-semibold uppercase tracking-wider text-muted">
                <tr>
                  <th scope="col" className="p-4">ID</th>
                  <th scope="col" className="p-4">University & Program</th>
                  <th scope="col" className="p-4">Location</th>
                  <th scope="col" className="p-4">Confidence</th>
                  <th scope="col" className="p-4">Extracted Fees & Scores</th>
                  <th scope="col" className="p-4">Extraction Notes</th>
                  <th scope="col" className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-quiet">
                {programs.map((program) => {
                  const isLowConf = program.confidence_score < 75.0;
                  return (
                    <tr key={program.id} className="hover:bg-[#fcfaf7]">
                      <td className="p-4 font-mono text-xs text-muted">#{program.id}</td>
                      <td className="p-4">
                        <span className="block font-serif font-semibold text-ink">{program.program_name}</span>
                        <span className="mt-0.5 block text-xs text-muted">{program.university_name}</span>
                      </td>
                      <td className="p-4 text-muted">
                        <span className="block font-medium">{program.country || "N/A"}</span>
                        <span className="text-xs uppercase">{program.degree_level}</span>
                      </td>
                      <td className="p-4 font-bold">
                        <span className={isLowConf ? "text-danger" : "text-amber-600"}>
                          {program.confidence_score}%
                        </span>
                      </td>
                      <td className="p-4 text-xs">
                        <p className="font-semibold text-ink">
                          Tuition: {program.tuition_fee !== undefined ? formatMoney(program.tuition_fee, program.currency) : "N/A"}
                        </p>
                        <p className="mt-0.5 text-muted">
                          GPA: {program.min_gpa ?? "N/A"} | IELTS: {program.min_ielts ?? "N/A"}
                          {program.dim_score_required && ` | DIM: ${program.dim_score_required}`}
                        </p>
                      </td>
                      <td className="max-w-xs p-4 text-xs leading-5 text-muted">
                        <p className="truncate" title={program.extraction_notes}>{program.extraction_notes || "Ambiguous fields detected."}</p>
                        {program.source_url && (
                          <a
                            href={program.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-1 inline-flex items-center gap-1 font-semibold text-accent underline"
                          >
                            Source link <ExternalLink size={10} />
                          </a>
                        )}
                      </td>
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            className="button-quiet text-xs"
                            onClick={() => openEditModal(program)}
                          >
                            <Edit3 size={14} aria-hidden="true" />
                            Inspect & Fix
                          </button>
                          <button
                            type="button"
                            className="button-primary text-xs"
                            onClick={() => void handleApproveAndPublish(program.id, {
                              university_name: program.university_name,
                              program_name: program.program_name,
                              tuition_fee: program.tuition_fee,
                              min_gpa: program.min_gpa,
                              min_ielts: program.min_ielts,
                              dim_score_required: program.dim_score_required,
                            })}
                            disabled={isVerifying}
                          >
                            Approve & Publish
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Inspect & Fix Modal */}
      {editingProgram && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true" aria-labelledby="edit-modal-title">
          <div className="panel-strong max-h-[90vh] w-full max-w-2xl overflow-y-auto p-6 sm:p-8">
            <div className="flex items-center justify-between border-b border-line pb-4">
              <div>
                <h2 id="edit-modal-title" className="font-serif text-2xl font-semibold">Inspect & Fix Program #{editingProgram.id}</h2>
                <p className="mt-1 text-sm text-muted">Correct extracted values before approving and publishing to student matching engine.</p>
              </div>
              <button
                type="button"
                className="text-muted hover:text-ink"
                onClick={() => setEditingProgram(null)}
              >
                ✕
              </button>
            </div>

            <div className="mt-4 border-l-4 border-amber-500 bg-[#fef8f0] p-4 text-xs leading-5 text-muted">
              <p className="font-semibold text-amber-800">Extraction Notes from AI Pipeline:</p>
              <p className="mt-1">{editingProgram.extraction_notes || "Low confidence score assigned due to missing explicit fields."}</p>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                void handleApproveAndPublish(editingProgram.id);
              }}
              className="mt-6 space-y-4 text-sm"
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="field-label" htmlFor="edit-uni">University Name</label>
                  <input
                    id="edit-uni"
                    className="field"
                    type="text"
                    value={editForm.university_name || ""}
                    onChange={(e) => setEditForm({ ...editForm, university_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor="edit-prog">Program Name</label>
                  <input
                    id="edit-prog"
                    className="field"
                    type="text"
                    value={editForm.program_name || ""}
                    onChange={(e) => setEditForm({ ...editForm, program_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor="edit-country">Country</label>
                  <input
                    id="edit-country"
                    className="field"
                    type="text"
                    value={editForm.country || ""}
                    onChange={(e) => setEditForm({ ...editForm, country: e.target.value })}
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor="edit-degree">Degree Level</label>
                  <select
                    id="edit-degree"
                    className="field"
                    value={editForm.degree_level || "master"}
                    onChange={(e) => setEditForm({ ...editForm, degree_level: e.target.value })}
                  >
                    <option value="bachelor">Bachelor</option>
                    <option value="master">Master</option>
                    <option value="phd">PhD</option>
                  </select>
                </div>
                <div>
                  <label className="field-label" htmlFor="edit-tuition">Tuition Fee</label>
                  <input
                    id="edit-tuition"
                    className="field"
                    type="number"
                    step="50"
                    value={editForm.tuition_fee ?? 0}
                    onChange={(e) => setEditForm({ ...editForm, tuition_fee: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor="edit-currency">Currency</label>
                  <input
                    id="edit-currency"
                    className="field"
                    type="text"
                    value={editForm.currency || "USD"}
                    onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor="edit-gpa">Minimum Required GPA</label>
                  <input
                    id="edit-gpa"
                    className="field"
                    type="number"
                    step="0.1"
                    min="0"
                    max="4"
                    value={editForm.min_gpa ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, min_gpa: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor="edit-ielts">Minimum Required IELTS</label>
                  <input
                    id="edit-ielts"
                    className="field"
                    type="number"
                    step="0.5"
                    min="0"
                    max="9"
                    value={editForm.min_ielts ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, min_ielts: Number(e.target.value) })}
                  />
                </div>

                {editForm.country === "Azerbaijan" && (
                  <div>
                    <label className="field-label" htmlFor="edit-dim">DIM Score Requirement (0-700)</label>
                    <input
                      id="edit-dim"
                      className="field"
                      type="number"
                      min="0"
                      max="700"
                      value={editForm.dim_score_required ?? ""}
                      onChange={(e) => setEditForm({ ...editForm, dim_score_required: Number(e.target.value) })}
                    />
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-3 border-t border-line pt-5">
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => setEditingProgram(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="button-primary"
                  disabled={isVerifying}
                >
                  {isVerifying ? "Saving & Publishing..." : "Approve & Publish"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

