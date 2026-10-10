# Live demo script

Seven minutes: 3 minutes of slides, then one minute for each of the four components below.
Each page has a **Try demo example** button that fills in the inputs listed here, so nothing has
to be typed on stage. The inputs live in `frontend/src/lib/demoExamples.ts`; change them there
and in this file together.

Results below were checked against the full Docker stack on 2026-10-10.

## Before you start

1. `docker compose up -d`, then wait about 30 seconds. Until the API is ready, pages answer
   "Backend error 500"; press Retry once it is up.
2. Open http://localhost:3000/api/v1/health. It should return OK.
3. Open the four pages in tabs, in order: `/plan`, `/target`, `/azerbaijan`, `/advisor`.

## 1. Route planner: `/plan` (minute 3–4)

Click **Try demo example**. The sentence is read immediately:

> Attestatım var, DİM balım 610, IELTS 6.5, ildə 8000 manat büdcəm var, kompüter elmləri oxumaq istəyirəm, bakalavr.

Expected: five values, each shown with the words it came from:

| Value | Source words |
|---|---|
| DİM 610 | "DİM balım 610" |
| IELTS 6.5 | "IELTS 6.5" |
| attestat | "Attestat" |
| bachelor | "bakalavr" |
| 8000 AZN | "8000 manat" |

Subject named: "kompüter elmləri". Then click **Show my options**: 12 routes.

Say: the reader is deterministic, with no LLM, so it shows exactly which words it read. The
planner doesn't say "you can't go to Germany". It shows the one-year bridge, what it costs, and
the official page that says so.

English sentence if asked:

> I finished school in Baku with an attestat, DIM score 610, IELTS 6.5, budget 8000 AZN a year. I want a bachelor's in computer science.

## 2. Target gap: `/target` (minute 4–5)

Click **Try demo example**. It fills in LMU Munich, Bachelor, Attestat, IELTS 6.5, DİM 610.
Then click **Analyze Target Gap**.

Expected: **ROUTE BLOCKED**, because LMU does not accept an 11-year attestat for direct entry.
Two bridges:

- Studienkolleg + Feststellungsprüfung: 12 months, TestAS, about 6,000–14,000 AZN.
- One year at an accredited Azerbaijani university: about 1,000–4,000 AZN.

The page also shows "Read from official portal, not yet human-verified" and "Last verified:
2026-09-02".

Point out: the language line stays UNKNOWN even with IELTS 6.5, because LMU asks for German B2.
The checklist doesn't count a test the university doesn't accept.

If there is time, click the **Bogazici University** quick pick to show an OPEN route.

## 3. Azerbaijan DİM cutoffs: `/azerbaijan` (minute 5–6)

Click **Try demo example**. It fills in UNEC, Group 1 (I qrup), score 610.

Expected: 16 UNEC Group 1 programmes.

| Verdict | Programmes |
|---|---|
| Too close to call | Information security 640.2, Information technology 634.6, Computer engineering 622.5 |
| Clears cutoff | Information security 609.2, Information technology 591.4, Computer science 583.1, Computer engineering 569.4 |
| Clears outright | Electrical & electronics engineering 417.8 and below |

Say: we tested machine learning honestly. For programmes with history, last year's cutoff had
an average error of 28.6 points against 34.9 for the best model, so that is what we show, with a
band from real errors. The trained model is kept for brand-new programmes; none exist today.

## 4. AI advisor: `/advisor` (minute 6–7)

Each example question is a button above the box. Clicking one fills the box; then click **Send**.
Enter adds a new line and does not send. Ask two or three:

| Question | Expected answer |
|---|---|
| Attestatla Münhen Texniki Universitetinə (TUM) bakalavra qəbul olmaq olar? | "Xeyr…" plus the Studienkolleg and Feststellungsprüfung route, in Azerbaijani, with 5 sources |
| What does Türkiye Bursları cover and what is the age limit? | Full tuition, monthly stipend, dormitory, health insurance, flights; under 21 for a bachelor's |
| Which German universities does the State Programme fund for master's study? | Humboldt, TUM, Tübingen, Giessen |
| Can you recommend a good pizza place in Baku? | "I do not have this information." It refuses rather than inventing an answer. |

## Only if asked: the agent at `/application`

The chat has one example button with the full profile ("…I want a bachelor's in Germany. What
are my routes?"). The agent calls the route engine as a tool, so it takes 8–15 seconds and its
wording varies between runs. The motivation-letter panel next to it is still placeholder data.

## Known rough edges

- The Azerbaijan page says "2026 Projections", but 2026 results were published in August.
- An off-topic advisor answer still lists 5 sources, even though it doesn't use them.
- Two tracker rows on `/applications` have a past deadline and show "0D LEFT".
