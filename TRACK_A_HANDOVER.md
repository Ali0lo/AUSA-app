# AUSA Track A patch — 15 September 2026

This archive contains only changed or new files relative to the uploaded AUSA.zip.
Use the project's own `docs/tracks/track-a-catalogue.md` as the scope: the supplied
Claude artifact link could not be accessed. The implementation is tested; the
unavailable evidence and human tasks below are explicitly unfinished. This is not a
claim of perfect software or a fully verified admissions dataset.

## Apply the patch

1. Extract this ZIP into a separate temporary folder first. Keep a backup of your
   current project and database before applying a schema migration.
2. From the extracted patch folder, run `python check_patch.py /path/to/your/AUSA`.
   On Windows, for example: `py -3.12 check_patch.py "C:\Projects\AUSA"`.
   This reads hashes only. A conflict means that file differs from the uploaded
   baseline: merge your teammate's edits with this patch before replacing it.
3. Copy the included files into the matching locations in your AUSA root. Do not
   delete other files. `PATCH_MANIFEST.json` lists every included file and its before/
   after SHA-256. Already-applied files are accepted by the check.
4. Use CPython **3.12** for the tested dependency set. The Windows launcher also accepts
   3.13, which was not executed in this Linux test environment. Keep your private
   `backend/.env` and `OPENAI_API_KEY`. No private environment file or key is included.
   An explicit `DATABASE_URL` is respected by the launcher. A local default setup still
   needs PostgreSQL with the pgvector extension available to the migration account.
5. Run `backend/run_backend.bat`, or from `backend`:

   ```bash
   python -m pip install -r requirements.txt -c constraints-tested.txt
   python -m scripts.bootstrap_catalogue
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

6. In `frontend`, run `npm ci`, then `npm run build` and `npm start` (or `npm run dev`
   for development). Keep the team's configured API URL and authentication secrets.
   Restart both services together: the new UI needs the new catalogue endpoints.

The launcher now uses Alembic plus deterministic CSV imports; it no longer runs the
optional LLM seeder on every launch. Existing document/vector records remain. RAG
ingestion and any model training are separate team workflows. Existing unversioned
databases matching the uploaded schema are recognised and adopted; unknown/customised
schemas stop with an explanation instead of being stamped blindly. The application
tracker table and unrelated team rows are preserved.

## Track A status

| Item | Delivered | Remaining evidence or limitation |
|---|---|---|
| A1 German prep year | Separate TUM and LMU one-year rows; original three FSP rows retained; demo names both | Subject-restricted recognition is inferred from university recognition policy plus the uni-assist/DAAD Azerbaijan result. Neither is a blanket admission promise. Individual assessment and human source review remain; Heidelberg's one-year row was not added. |
| A2 Existing-row costs | All 15 original rows have a tuition/currency pair or explicit unknown-cost notes; cost, fee, deadline and scope render in cards | Original facts were preserved, not silently re-certified. A general recognition page may not state programme fees; this does not prove fees are absent elsewhere. Complete cost-to-degree ranking remains unavailable. |
| A3 Master's catalogue | 30 distinct programmes across CN, TR, GB, DE, US and PL; all use bachelor_degree; demo and API tests return named TR/GB/CN universities | Programme fit, recognition, language subscores and selection still require confirmation. |
| A4 US and Poland | Five CMU master's programmes; one SGGW programme; all eight Polish DP entries across three institutions restored | Poznań and Kraków admissions pages could not provide usable verified evidence; details below. SGGW's current title differs from the DP title. US entries concern 2027 intake; DP entries are 2026. |
| A5 Funding sources | Türkiye Bursları, Chevening and NAWA corrected from primary sources, with URLs and dated provenance | Human sign-off pending. SOCAR current call unavailable; Fulbright source returned 403. These conditions remain unresolved. |
| A6 DİM spot-check | Reproducible 30-row sampling tool and review instructions | **Unfinished: actual cutoff CSV/publication pages absent; 0/30 reviewed.** No match rate claimed. |

Master's coverage: USTC 7, Zhejiang 5, ITU 5, UCL 3, TUM 4, Carnegie Mellon 5,
SGGW 1. Total catalogue: **47 requirement rows, comprising 17 bachelor and 30 master**.
The two DP CSVs contain **4,121 programme entries**; this is not an award count.

Every added admission row remains `claude-extracted`, awaiting a real reviewer. The
original rows retain their provenance. `/admin` now has a separate admission catalogue
queue using `program_requirements`; the existing flagged-programme queue still works
with its original table. Add actual reviewer emails to the existing `ADMIN_EMAILS`
setting, sign in, inspect the evidence and approve there. CSV files cannot impersonate
reviewers. Reimports preserve review for identical facts and clear it when facts change.

## Source findings and unavailable pages

- Germany: [uni-assist Azerbaijan recognition result](https://www.uni-assist.de/en/tools/check-university-admission/?lid=5249&lvl=5)
  supports subject-restricted access after a successfully completed full-time academic
  year at a recognised university for the specified modern 11-year Attestat. University
  policy and individual document evaluation still apply. Exact university URLs and
  field-level evidence are in the CSV.
- Türkiye: [scholarship criteria](https://www.turkiyeburslari.gov.tr/scholarshipsprograms)
  and [full-time programmes](https://www.turkiyeburslari.gov.tr/fulltimeprograms) support
  under 21 for bachelor and under 30 for master, plus other academic and citizenship
  conditions. The published recurring window is not a promise of a future open call.
- [Chevening eligibility](https://www.chevening.org/resource-hub/guidance/eligibility/):
  2,800 hours must be gained after the undergraduate degree. Total lifetime work hours
  alone are insufficient; graduation timing and other conditions remain unresolved.
- [NAWA's 2026 Banach call](https://nawa.gov.pl/images/Banach/2026/Banach-2026---Call-for-applications-EN.pdf)
  resolves the conflicting exclusive field lists: neither earlier list is enforced.
  Eligible institutions, degree date, language and other conditions apply; the 2026
  call is closed. The [programme page](https://nawa.gov.pl/en/students/foreign-students/the-banach-scholarship-programme)
  states PLN 2,500 monthly support; tuition exemption applies under its public-university
  conditions, not universally to every programme.
- Poland: [SGGW's Sustainable Horticulture page](https://www.sggw.edu.pl/en/kierunki-sggw/sustainable-horticulture/)
  supports a real English master's row. DP lists **Horticulture**, so funding equivalence
  is unconfirmed. Poznań's older `www.puls.edu.pl/en/` returned 502; the replacement
  `up.poznan.pl` robots check returned 500, so the project collector did not proceed.
  Kraków's `urk.edu.pl` access was blocked by robots restrictions. Their DP programmes
  remain available, with admission requirements unavailable. No bypass or invented row.
- SOCAR: no current official scholarship call was established. Previously unverified
  age/language thresholds no longer cause automatic rejection. Existing employment/level
  assumptions still need source review. [Fulbright's embassy page](https://az.usembassy.gov/fulbright-foreign-student-program/)
  returned 403; no experience minimum is asserted from that failed retrieval.

The CSV evidence fields cite the USTC and Zhejiang programme PDFs, UCL degree/language
pages, TUM programme/fee pages, ITU programme catalogue/admissions guide and CMU programme
pages. Important distinctions are retained: ITU programmes are 30% English; TUM Robotics
requires German and English; UCL Computer Science is a conversion programme; some
Zhejiang programmes require supervisor acceptance. Unknown application/living costs
remain blank. Old deadlines are labelled expired instead of treated as open.

## Integration boundaries

Target mode now queries the database by university and degree level and reassesses when
inputs change. It retains the gap/checklist/process/alternative-university structure.
Unknown universities and API failures have visible states and retry; late responses
cannot replace a newer profile. Added API fields are optional for existing clients.
Country route status still describes a possible pathway, not confirmed individual
admission. DP listing, scholarship eligibility and admission are separate facts.

The legacy TOEFL field explicitly accepts the 0–120 scale; comparison of 1–6 results is
unavailable. Reliable cost ranking, missing DİM data and broader Track B/C/D features
have not been invented. Small fixes in the admin/applications/tracker UI were required
to make the existing lint/type/build gates pass; those workflows were regression-tested.

See `TRACK_A_TEST_RESULTS.md` for executed checks and limits. Native Windows execution,
the team's actual database/customisations and paid live OpenAI calls were not available
for validation. No test suite can establish that bugs are impossible.
