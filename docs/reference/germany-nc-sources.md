# German NC data: what is actually published, and where

**Status:** reconnaissance, 30 August 2026. Every claim below was verified by fetching the
page named. Nothing here is inferred from a search-result snippet.

> **Correction, 31 August 2026 — this survey asked the wrong question.**
> It measured *how many years of NC values* a university publishes. Verified the next day on
> the same Marburg page: the published tables carry the footnote *"Anzahl der gültigen
> Bewerbungen (ohne Bildungsausländer\*innen)"* — they **exclude international applicants**,
> who are allocated from a separate quota of roughly 5–8% of places. So archive depth in the
> main tables measures a threshold our students are never ranked against.
>
> The same page also publishes a separate `Zulassungsverfahren der Ausländer*innen` section
> with its own per-programme values — Humanbiologie **1.6** for WS 2025/26, **1.4** for
> WS 2024/25 — and, for many programmes, the outcome *"Es konnten alle Bewerbungen zugelassen
> werden"*: every application admitted. **That** section is the one that matters.
>
> **The survey question is therefore: does this university publish its international-quota
> outcome, and how far back?** Not how deep the main NC archive runs. The table below stays
> because the format and robots findings are still accurate, but its depth column measures
> the wrong series. See [ADR-0008](../adr/0008-selectivity-replaces-cutoff-prediction.md).

**Why this document exists.** `backend/scripts/collect_germany.py` was deleted on 30 August
because all three of its target URLs were invented — every fetch 404'd and an
`except Exception: pass` fell through to a mock-HTML constant, so the collector could never
have returned real data and its passing run proved nothing. This file is the survey that
should have preceded it. No German collector should be written against an unverified URL
again.

**Why Germany matters now.** ADR-0007 §3 was corrected on 30 August to remove Azerbaijan
from the "Your chances" block. That block now rests on Germany and Poland, and we have
zero collected cutoff rows for either. Germany is no longer cuttable (ADR-0007 §12).

---

## The headline finding: the obvious source is the wrong one

The intuitive plan is "collect from hochschulstart.de, it's the official central portal."
That plan is wrong twice over.

### 1. hochschulstart covers four subjects, and they are the four our students can least use

Verified on the hochschulstart.de homepage: central allocation applies to **Human medicine,
Veterinary medicine, Dentistry and Pharmacy** only. Everything else is allocated by the
universities themselves, which merely transmit results to hochschulstart afterwards.

Those four subjects are the least reachable route for an Azerbaijani school-leaver: they
are taught in German, they require C1 plus (for most applicants with a 11-year attestat) a
Studienkolleg year, and the best-grade quota NC sits around 1.0–1.2 — roughly the top of
the German grade scale. Building our German capability on this corpus would repeat the
ADR-0007 §3 error in a new place: optimising for the best-evidenced data rather than for
what the student asked.

### 2. Its files sit behind the one path its robots.txt disallows

```
hochschulstart.de/robots.txt
  User-agent: *
  Disallow: /fileadmin/
  Disallow: /typo3conf/
```

No AI-specific rules, no `Content-Signal`, no TDM reservation — permissive in every respect
except that one path. And every statistics PDF on the site lives under it:

```
/fileadmin/media/dosv/statistik/SfH_Statistik_Kennzahlen_WiSe2025_26.pdf
/fileadmin/media/dosv/statistik/SfH_Statistik_Kennzahlen_SoSe2026.pdf
```

So an automated collector walking those PDFs is doing exactly what the site's robots.txt
asks crawlers not to do. **Do not write one.** If we ever need this corpus, a person
downloads the PDFs and a script parses the local files — robots.txt governs automated
crawling, not a human reading a public document. That distinction is the whole of the
allowance; a script that fetches the URL is not covered by it.

Archive depth, for the record, should it ever be wanted: general statistics from SoSe 2020
onward; per-procedure Auswahlgrenzen PDFs through WiSe 2019/20; historical series back to
SoSe 2015. A procedural reform at SoSe 2020 changed how results are reported, so the series
is **not continuous across that boundary** — anything spanning it needs the break modelled,
not smoothed.

---

## Where the usable data actually is: individual university NC pages

These are official first-party sources, they are HTML rather than PDF, they carry the
subjects students actually apply to, and some of them go back further than any other
dataset in this project.

**The catch is that depth varies enormously between universities, and this is the single
most important fact for planning.** Two verified samples at the extremes:

| University | Depth | Format | Coverage |
|---|---|---|---|
| Marburg | **WS 2009/10 → WS 2026/27 — 17 years** | HTML tables in-page | selected subjects; medicine etc. handed off to hochschulstart |
| Duisburg-Essen | **one semester, WS 2014/15 — and stale** | HTML tables by faculty | ~60 programmes |

Both publish per-programme rows with a numeric grade threshold and a Wartesemester
threshold. Verbatim from Duisburg-Essen, showing the shape:

```
Betriebswirtschaftslehre   | 2,5          | 6 WS und Note 3,1  | zulassungsbeschränkt
Medizinische Biologie      | 1,4 und 2 WS | 10 WS und Note 1,9 | zulassungsbeschränkt
```

Note the second row: the threshold is a **grade-and-wait pair**, not a scalar. A row can
read "1,4 with 2 waiting semesters", which is not a single number and does not fit
`cutoff_value: float` without a decision about what we store. That decision is not made
here.

`uni-marburg.de/robots.txt` disallows only search, PDF-generation and a few HRZ service
paths; `/studium/` is not restricted, and there are no AI-specific rules.

---

## What this changes about the plan

**The survey comes before the collector.** We do not yet know how many German universities
publish a Marburg-style multi-year archive versus a Duisburg-Essen-style single semester.
That ratio decides whether Germany can carry a genuine success rate at all, because
`P(next year's cutoff ≤ your score)` is learnable only from cutoff *variance over years* —
one semester per university gives a number to display and nothing to regress on.

So the first German task is not scraping. It is: **for a defined list of German
universities, record where their NC page is and how many years it holds.** The output is a
table of university → URL → year range → format, and it is what tells us whether the
"Your chances" block can be honest for Germany.

**One collector will not work.** Each university's page is its own layout. Per ADR-0007 §11
this is the auto-discover / human-review / script-the-rest shape, and the per-university
history depth belongs in the survey table as data, not as an assumption baked into code.

**`auswahlgrenzen.de` is a discovery index, not a source.** It is a directory of direct
links to universities' own original NC lists. Using it to *find* official URLs is
legitimate; extracting values from it is not, and would violate the official-sources-only
rule. Same standing as a search engine.

**`nc-werte.info` remains excluded** as an aggregator, per the existing constraint.
`studis-online.de` is the same category and is excluded on the same grounds.

---

## Open questions this survey did not answer

- How deep is the *typical* German university archive? Two samples at opposite extremes do
  not give a distribution. This is the question the survey exists to answer.
- How is a "grade + Wartesemester" pair stored in `program_cutoff_history`, whose
  `cutoff_value` is a single Float? Wartesemester was abolished as a federal quota in the
  2020 reform but still appears in university tables, including for recent semesters.
- Which German programmes are **zulassungsfrei** (no NC at all)? For those, the honest
  second number is not a probability — admission is gated by language level, Studienkolleg
  and APS instead. That is a different card, and it may well be the most common case in
  exactly the engineering and CS subjects our students want.
- Does the SoSe 2020 procedural reform have a per-university analogue, or is it confined to
  the centrally-allocated four?
