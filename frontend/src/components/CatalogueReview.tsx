"use client";
import { useEffect, useState } from "react";
import { fetchCatalogueReview, verifyCatalogueRow, getUserFacingError, type CatalogueReview as Review } from "@/lib/api";

export function CatalogueReview({ token }: { token?: string }) {
  const [level, setLevel] = useState<"bachelor" | "master">("bachelor");
  const [reload, setReload] = useState(0);
  return <section className="panel p-5 my-6" aria-label="Admission catalogue review">
    <h2 className="section-heading text-2xl">Admission catalogue review</h2>
    <p className="mt-2 text-sm text-muted">Review the original sources and every populated field. Corrections belong in the curated CSV; import it and reload this queue before approving.</p>
    <label htmlFor="review-level" className="field-label mt-3">Degree level</label>
    <select id="review-level" className="field" value={level} onChange={(e) => setLevel(e.target.value as "bachelor" | "master")}>
      <option value="bachelor">Bachelor</option><option value="master">Master</option>
    </select>
    <button type="button" className="button-secondary mt-3" onClick={() => setReload((n) => n + 1)}>Reload review queue</button>
    <ReviewQueue key={JSON.stringify([level, token, reload])} level={level} token={token} />
  </section>;
}

function ReviewQueue({ level, token }: { level: "bachelor" | "master"; token?: string }) {
  const [rows, setRows] = useState<Review[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<number | null>(null);
  const [confirmed, setConfirmed] = useState<Record<number, boolean>>({});
  useEffect(() => {
    let active = true;
    fetchCatalogueReview(level, token).then((data) => { if (active) setRows(data); })
      .catch((e) => { if (active) setError(getUserFacingError(e, "Catalogue review").message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [level, token]);

  async function verify(row: Review) {
    const id = row.requirement.id;
    if (id == null || !confirmed[id]) return;
    setPending(id); setError("");
    try {
      await verifyCatalogueRow(id, row.revision, token);
      setRows((current) => current.filter((r) => r.requirement.id !== id));
    } catch (e) { setError(getUserFacingError(e, "Catalogue review").message); }
    finally { setPending(null); }
  }
  return <div>
    {loading && <p className="mt-3" role="status">Loading catalogue review…</p>}
    {error && <p className="notice-error mt-3" role="alert">{error}</p>}
    {!loading && !error && !rows.length && <p className="mt-3">No pending catalogue rows at this level.</p>}
    {rows.map((row) => <article className="border-t border-quiet mt-5 pt-4" key={row.requirement.id}>
      <h3 className="font-semibold">{row.requirement.university_name} — {row.requirement.program_name}</h3>
      <p className="text-sm text-muted">{row.requirement.intake_year} · {row.requirement.entry_qualification_accepted?.replace(/_/g, " ")}</p>
      <dl className="my-3 text-sm space-y-1">{Object.entries(row.requirement).filter(([key]) => !["evidence", "checks", "id"].includes(key)).map(([key, value]) => <div key={key} className="break-words"><dt className="inline font-semibold">{key.replace(/_/g, " ")}: </dt><dd className="inline">{value == null ? "Unknown" : Array.isArray(value) ? value.join(", ") : String(value)}</dd></div>)}</dl>
      {row.requirement.evidence?.map((item, i) => <p className="text-sm mt-2" key={i}><a className="text-link" href={/^https?:\/\//i.test(item.url) ? item.url : undefined} target="_blank" rel="noreferrer noopener">Open evidence: {item.fields.join(", ")}</a> — {item.note} ({item.checked_at})</p>)}
      <label className="flex gap-2 mt-3 text-sm"><input type="checkbox" checked={confirmed[row.requirement.id!] ?? false}
        disabled={pending !== null || !row.requirement.evidence?.length}
        onChange={(e) => setConfirmed((current) => ({ ...current, [row.requirement.id!]: e.target.checked }))} />I opened the sources and checked these facts and caveats.</label>
      <button className="button-primary mt-3" type="button" disabled={pending !== null || !confirmed[row.requirement.id!]}
        onClick={() => void verify(row)}>{pending === row.requirement.id ? "Saving…" : "Verify this catalogue row"}</button>
    </article>)}
  </div>;
}
