"use client";
import { useEffect, useState, type ReactNode } from "react";
import { assessCatalogue, fetchCatalogue, getUserFacingError, type CatalogueResult } from "@/lib/api";
import type { AssessRoutesPayload, RouteUniversity } from "@/types";

export function CatalogueTarget({ university, onUniversity, profile, renderUniversity }: {
  university: string;
  onUniversity: (name: string) => void;
  profile: AssessRoutesPayload;
  renderUniversity: (row: RouteUniversity) => ReactNode;
}) {
  const [options, setOptions] = useState<{ level: string; items: RouteUniversity[] }>();
  const [response, setResponse] = useState<{ key: string; data?: CatalogueResult; error?: string }>();
  const [retry, setRetry] = useState(0);
  const serialized = JSON.stringify(profile);
  const requestKey = JSON.stringify([university, serialized, retry]);
  const known = options?.level === profile.level_sought ? options.items : [];
  const names = [...new Set(known.map((row) => row.university_name))].sort();
  const current = response?.key === requestKey ? response : undefined;
  const loading = !current;
  const data = current?.data;
  const error = current?.error;

  useEffect(() => {
    let active = true;
    fetchCatalogue(profile.level_sought).then((result) => {
      if (active) setOptions({ level: profile.level_sought, items: result.items });
    }).catch(() => { /* The assessment below reports the actionable connection error. */ });
    return () => { active = false; };
  }, [profile.level_sought, retry]);

  useEffect(() => {
    let active = true;
    const timer = setTimeout(() => {
      assessCatalogue(university, JSON.parse(serialized)).then((result) => {
        if (active) setResponse({ key: requestKey, data: result });
      }).catch((caught) => {
        if (active) setResponse({ key: requestKey, error: getUserFacingError(caught, "University requirements").message });
      });
    }, 250);
    return () => { active = false; clearTimeout(timer); };
  }, [university, serialized, requestKey]);

  return <section className="panel p-5" aria-label="Target university requirements">
    <p className="eyebrow">Target roadmap</p>
    <h2 className="section-heading mt-2 mb-4">{university || "Choose a university"}</h2>
    <label className="field-label" htmlFor="target-uni-select">Select or name a university to target</label>
    <input id="target-uni-select" className="field" list="catalogue-universities" value={university}
      onChange={(event) => onUniversity(event.target.value)} />
    <datalist id="catalogue-universities">{names.map((name) => <option key={name} value={name} />)}</datalist>
    <p className="mt-2 text-sm text-muted">{profile.level_sought === "master" ? "Master’s" : "Bachelor’s"} requirements from the current catalogue. A qualification match does not guarantee admission.</p>
    <h3 className="font-semibold mt-5">1. Gap Statement</h3>
    <div aria-live="polite">
      {loading && <p className="mt-4" role="status">Checking university requirements…</p>}
      {error && <div className="notice-error mt-4"><p>{error}</p><button type="button" className="button-secondary mt-2" onClick={() => setRetry((n) => n + 1)}>Retry catalogue</button></div>}
      {!loading && !error && data && !data.items.length && <p className="mt-4">Requirements for this university and level have not been collected. This is a catalogue gap; ask the university about admission.</p>}
      {!loading && !error && data?.items.map((row) => <div key={row.id ?? `${row.program_name}:${row.entry_qualification_accepted}`}>
        {renderUniversity(row)}
      </div>)}
    </div>
    <h3 className="font-semibold mt-5">2. Requirement Checklist</h3>
    <p className="mt-2 text-sm text-muted">The programme cards list recorded documents, scores and caveats. Confirm subject eligibility, language subscores and certificate recognition with the university. Unrecorded requirements still need checking.</p>
    <h3 className="font-semibold mt-5">3. Process Checklist &amp; Deadlines</h3>
    <ol className="list-decimal pl-5 mt-2 space-y-2 text-sm">
      <li>Open the programme’s cited sources and confirm the intended intake.</li>
      <li>Check its entry conditions, document list, applicable fees and application deadline.</li>
      <li>Use the application portal named in the programme card after confirming those conditions.</li>
    </ol>
    {!loading && data?.items.length ? <>
      <h3 className="font-semibold mt-5">4. Other universities to investigate</h3>
      <p className="text-sm text-muted mt-2">Other catalogue entries at this level and destination; admission and subject fit need their own checks.</p>
      <div className="flex flex-wrap gap-2 mt-2">{[...new Set(known.filter((row) => row.university_name !== university && data.items.some((item) => item.country_code === row.country_code)).map((row) => row.university_name))].slice(0, 4).map((name) => <button key={name} type="button" className="button-secondary" onClick={() => onUniversity(name)}>{name}</button>)}</div>
    </> : null}
    <p className="mt-5 text-xs text-muted"><strong>Target roadmap methodology notice:</strong> This compares recorded requirements with your current inputs. It does not predict admission or establish scholarship eligibility. A missing catalogue entry means requirements remain unavailable.</p>
  </section>;
}
