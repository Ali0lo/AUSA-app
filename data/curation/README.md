# Curating `program_requirements`

This is the one task in the project that writing more code cannot speed up, and it gates
four of the six countries. Everything else — the route engine, the two-hop composition,
the endpoint — is built and waiting on these rows.

**Deadline: 15 September 2026.** Target: ~50 rows. Split across four people that is 12–13
rows each, and one university's page usually yields several rows.

## The one rule that matters

**A blank cell means "we do not know". It never means "not required".**

If you cannot find a programme's IELTS minimum, leave `language_minimum_score` empty. Do
not write 6.0 because it is usually 6.0. Do not write 0. Do not write "N/A". The engine
treats a blank as an unconfirmed requirement and will never tell a student they are
eligible on the strength of it — which is correct, and is the whole point. A guessed 6.0
tells a student with 5.5 they can apply, and they cannot.

This is not a style preference. This branch deleted an entire module for inventing an
IELTS of 6.0 for students who never sat the exam, and quarantined database rows written
by a fallback that invented programme requirements. Do not reintroduce by hand what was
just removed in code.

If you are unsure whether something is a genuine absence or a gap in your search: it is a
gap. Leave it blank.

## Where the data may come from

**Only the university's own official page, or the official national admissions body.**
Put that exact URL in `source_url`. One row, one page you actually opened.

Forbidden as sources — these are not style guidance, they are legal and ethical limits:

| Source | Why |
|---|---|
| **qebulai.az** | robots.txt disallows our crawlers, `Content-Signal: ai-train=no`, express reservation under Article 4 of EU Directive 2019/790. Also a direct competitor. **Do not use, by hand or by script.** |
| **hochschulstart.de `/fileadmin/`** | Disallowed by robots.txt — and every statistics PDF lives there. |
| **DAAD scholarship database** | Explicitly disallowed (`/deutschland/foerderung/stipendiendatenbank/00462.*`). DAAD's terms of use have not been read; read them before any bulk fetch. Main host sets `Crawl-delay: 2`. |
| **nc-werte.info, studis-online.de, auswahlgrenzen.de, CUCAS** | Aggregators. Use them ONLY to discover an official URL, never as the source itself. Never cite them in `source_url`. |

sec.az explicitly allows our crawlers and is fine.

## Filling the columns

**Required — a row without these is rejected:** `university_name`, `program_name`,
`level`, `intake_year`, `country_code`, `provenance`, `source_url`, `retrieved_at`.

**`level` is part of the key, not a label.** The same university at bachelor and master is
two rows, and the requirements genuinely differ. Findings in this project *invert* between
the two levels — Germany and the UK are closed to an Azerbaijani school-leaver but open to
a bachelor holder. Never copy a master row down to bachelor.

**`university_name` and `program_name` must match the DP catalogue exactly.** Joins are by
exact name match. Copy the name from `data/raw/azerbaijan/dp-*.csv`, not from the
university's own site, where it may differ. A mismatched name silently matches nothing.

**`entry_qualification_accepted`** — one of exactly these, no free text:
`attestat`, `one_year_university`, `a_level`, `ib`, `foundation_year`,
`feststellungspruefung`, `bachelor_degree`.

**`tuition_per_year` must be the INTERNATIONAL figure.** The domestic or EU number is
usually the more prominent one on the page and is the wrong one for our students. If the
page shows only a domestic figure, leave tuition blank rather than copying it.

**`gpa_minimum` needs `gpa_scale`** (`4.0`, `5.0`, `100`). A GPA without its scale is not a
number, and mixing scales silently is how a 3.0 becomes a rejection.

**`provenance` and `verified_by`** — if a person read the official page, that is
`human-verified`, and put your name in `verified_by`. Those are the only circumstances.
Never fill `verified_by` for a row you did not personally check against the source.

**Booleans** (`foundation_required`) carry a real distinction: blank = unknown, `False` =
we checked and it is genuinely not required. Use `False` only when the page says so.

## Priority worklist

Ranked by how many DP-funded programmes each university covers, so the early rows buy the
most. **These 30 universities cover 58.7% of the 2,293 funded programmes** in the six
target countries.

Two facts worth knowing before you start, both verified against the catalogue: **the DP
funds zero bachelor places in the USA and zero in Poland** — that is a real answer, not a
gap, so do not go looking. Poland has 8 master programmes across 3 universities, total.

| # | Country | Bachelor | Master | Total | Cumulative | University |
|---:|:--:|---:|---:|---:|---:|---|
| 1 | CN | 19 | 68 | 87 | 3.8% | Zhejiang University |
| 2 | TR | 29 | 45 | 74 | 7.0% | Istanbul Technical University |
| 3 | CN | 35 | 34 | 69 | 10.0% | Tsinghua University |
| 4 | GB | 19 | 50 | 69 | 13.0% | Imperial College London |
| 5 | TR | 24 | 43 | 67 | 16.0% | Ankara University |
| 6 | CN | 5 | 58 | 63 | 18.7% | University of Science and Technology of China |
| 7 | GB | 20 | 40 | 60 | 21.3% | UCL |
| 8 | GB | 33 | 27 | 60 | 23.9% | University of Edinburgh |
| 9 | DE | 13 | 43 | 56 | 26.4% | Technical University of Munich |
| 10 | TR | 20 | 29 | 49 | 28.5% | Middle East Technical University |
| 11 | CN | 3 | 46 | 49 | 30.7% | Wuhan University |
| 12 | GB | 20 | 27 | 47 | 32.7% | University of Cambridge |
| 13 | CN | 34 | 13 | 47 | 34.8% | Harbin Institute of Technology |
| 14 | GB | 19 | 28 | 47 | 36.8% | University of Manchester |
| 15 | CN | 17 | 23 | 40 | 38.6% | University of Hong Kong |
| 16 | TR | 0 | 38 | 38 | 40.2% | Ege University |
| 17 | CN | 12 | 24 | 36 | 41.8% | Xiamen University |
| 18 | CN | 14 | 22 | 36 | 43.3% | Shanghai University |
| 19 | CN | 9 | 24 | 33 | 44.8% | Shanghai Jiao Tong University |
| 20 | CN | 7 | 25 | 32 | 46.2% | Xi'an Jiaotong University |
| 21 | CN | 12 | 19 | 31 | 47.5% | Tianjin University |
| 22 | GB | 4 | 27 | 31 | 48.9% | University of Glasgow |
| 23 | CN | 19 | 10 | 29 | 50.2% | Beijing University of Chemical Technology |
| 24 | GB | 5 | 24 | 29 | 51.4% | University of Birmingham |
| 25 | CN | 13 | 15 | 28 | 52.6% | Chinese University of Hong Kong |
| 26 | TR | 10 | 18 | 28 | 53.9% | Boğaziçi University |
| 27 | TR | 1 | 27 | 28 | 55.1% | Gazi University |
| 28 | US | 0 | 28 | 28 | 56.3% | University of Michigan-Ann Arbor |
| 29 | GB | 8 | 19 | 27 | 57.5% | University of Oxford |
| 30 | DE | 0 | 27 | 27 | 58.7% | RWTH Aachen University |

### Suggested split

China is the largest single block and is also the least-modelled entry route — the spec
records that whether an Azerbaijani attestat gives direct entry to Chinese universities
outside CSC is **unchecked**, and it is the same question that turned out to close Germany
and the UK. Whoever takes China should answer that question first, for one university,
before curating thirty rows on an assumption.

- **Person A — China** (rows 1, 3, 6, 11, 13): start with the entry-route question above.
- **Person B — UK** (rows 4, 7, 8, 12, 14): the UK is only reachable after the prep year;
  confirm each page's stance on a one-year-completed Azerbaijani applicant.
- **Person C — Turkey** (rows 2, 5, 10, 16, 26): check whether TR-YÖS is required or
  waived, per university. This varies and it decides whether the route is open.
- **Person D — Germany + USA + Poland** (rows 9, 28, 30 + the 3 Polish universities):
  Germany needs the APS/Studienkolleg position stated explicitly.

## When you are done

Save as `data/curation/program_requirements_<yourname>.csv` using the template's exact
header, and say so — a loader for these rows does not exist yet and is a small task once
the first real file exists. Do not hand-write rows into the database.

Sanity check before you submit: does every row have a `source_url` you personally opened,
and is every blank cell a genuine "we do not know" rather than a cell you skipped?
