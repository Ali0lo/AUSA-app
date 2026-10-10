"""
Build the document advisor's knowledge base (university_documents) from sourced data.

Every document is rendered from a row that already carries its source URL:
  * program_requirements -- one document per university requirement row
  * ALL_GLOBAL_SCHOLARSHIPS -- one document per scholarship
  * dp_catalogue -- one document per (level, country, university) funded list

Nothing is written by hand here. A field the source did not state is rendered as
"not stated", never dropped, so the advisor cannot read an absence as a rule.

Needs OPENAI_API_KEY, so it runs in the api container:
    docker compose exec api python -m scripts.index_documents

Re-running replaces the documents this script wrote (metadata.origin) and nothing else.
If an embedding fails the transaction rolls back; no document is stored without a vector.
"""

import asyncio
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.domain.global_scholarships import ALL_GLOBAL_SCHOLARSHIPS
from app.models.document import UniversityDocument
from app.models.dp_catalogue import DPCatalogueEntry
from app.models.qualifications import ProgramRequirement
from app.services.embeddings import MODEL, _require_api_key

ORIGIN = "index_documents"
BATCH_SIZE = 100
NOT_STATED = "not stated"

# The codes in program_requirements.entry_qualification_accepted, in words. Embeddings
# and the answering model both read "one_year_university" poorly; they read this well.
QUALIFICATION_WORDS = {
    "attestat": "the Azerbaijani school attestat (11-year school certificate)",
    "one_year_university": "one completed year at a recognised university (for example a first year in Azerbaijan)",
    "a_level": "A-levels",
    "ib": "the IB Diploma",
    "foundation_year": "a completed foundation year",
    "feststellungspruefung": "the Feststellungsprüfung, the exam at the end of a Studienkolleg",
    "bachelor_degree": "a completed bachelor's degree",
}


def _v(value: Any, suffix: str = "") -> str:
    if value is None or value == "":
        return NOT_STATED
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value}{suffix}"


def render_requirement(row: Any) -> Dict[str, Any]:
    level = "bachelor's" if row.level == "bachelor" else "master's"
    language = row.language_test or NOT_STATED
    if row.language_test and row.language_minimum_score is not None:
        language += f", minimum score {_v(row.language_minimum_score)}"
    exam = row.entrance_exam or NOT_STATED
    if row.entrance_exam and row.entrance_exam_minimum is not None:
        exam += f", minimum score {_v(row.entrance_exam_minimum)}"
    gpa = f"{_v(row.gpa_minimum)} on a {row.gpa_scale} scale" if row.gpa_minimum is not None else NOT_STATED
    tuition = f"{_v(row.tuition_per_year)} {row.currency or ''}".strip() if row.tuition_per_year is not None else NOT_STATED
    accepted = row.entry_qualification_accepted
    if accepted is None:
        entry = "Which school or university qualification this route accepts: not stated."
    else:
        entry = f"This route admits applicants who hold {QUALIFICATION_WORDS.get(accepted, accepted)}."
        if accepted != "attestat":
            entry += " The Azerbaijani school attestat on its own is not what this route accepts."
    lines = [
        f"{row.university_name} ({row.country_code}) -- {row.program_name}, {level} admission for {row.intake_year} intake, international applicants.",
        entry,
        f"Foundation year required: {_v(row.foundation_required)}. Foundation providers: {_v(row.foundation_providers)}.",
        f"Language requirement: {language}. Language of instruction: {_v(row.language_of_instruction)}.",
        f"Entrance exam: {exam}.",
        f"Minimum GPA: {gpa}.",
        f"Tuition per year for international students: {tuition}. Application fee: {_v(row.application_fee)}.",
        f"Application deadline: {_v(row.application_deadline)}. Application portal: {_v(row.application_portal)}.",
        f"Documents required: {_v(row.documents_required)}.",
    ]
    if row.notes:
        lines.append(f"Notes: {row.notes}")
    lines.append(f"Data status: {row.provenance} (not yet checked by a person)." if row.provenance == "claude-extracted"
                 else f"Data status: {row.provenance}.")
    return {
        "content": "\n".join(lines),
        "metadata": {
            "origin": ORIGIN, "kind": "university_requirement",
            "university": row.university_name, "country": row.country_code,
            "level": row.level, "provenance": row.provenance, "source_url": row.source_url,
        },
    }


def render_scholarship(s: Any) -> Dict[str, Any]:
    ages = ", ".join(
        f"{label} under {limit}" for label, limit in
        (("bachelor", s.age_limit_bachelor), ("master", s.age_limit_master)) if limit
    ) or NOT_STATED
    lines = [
        f"Scholarship: {s.name} ({s.native_name}), provided by {s.provider}, for study in {s.country_name}.",
        f"Coverage: {s.coverage_summary}. Tuition covered: {_v(s.tuition_coverage_pct, '%')}. "
        f"Monthly stipend: {_v(s.stipend_monthly_local)}.",
        f"Minimum GPA: {_v(s.min_gpa)}{' on a ' + s.min_gpa_scale + ' scale' if s.min_gpa and s.min_gpa_scale else ''}. "
        f"Minimum IELTS: {_v(s.min_ielts)}. Minimum TOEFL: {_v(s.min_toefl)}. Age limits: {ages}.",
        f"Work experience required: {_v(s.work_experience_hours, ' hours')}. Return-service obligation: {_v(s.return_service_obligation)}.",
        f"Application window: {s.application_window_start} to {s.application_window_end}.",
        f"Places for Azerbaijani applicants: {_v(s.azerbaijan_quota_or_seats)}.",
        "Eligibility: " + "; ".join(s.eligibility_criteria) + ".",
        "Documents required: " + "; ".join(s.required_documents) + ".",
        "Selection stages: " + "; ".join(s.selection_stages) + ".",
        f"Citation: {s.citation}",
    ]
    return {
        "content": "\n".join(lines),
        "metadata": {
            "origin": ORIGIN, "kind": "scholarship", "scholarship": s.name,
            "country": s.country_name, "provenance": s.provenance,
            "source_url": s.official_guidelines_url or s.official_portal_url,
        },
    }


def render_dp_groups(rows: List[Any]) -> List[Dict[str, Any]]:
    groups: Dict[tuple, List[Any]] = defaultdict(list)
    for r in rows:
        groups[(r.level, r.country_source, r.university_name, r.intake_year, r.source_url)].append(r)
    docs = []
    for (level, country, university, year, source_url), items in sorted(groups.items()):
        programmes = sorted({i.program_name for i in items})
        level_label = "bachelor's" if level == "bachelor" else "master's"
        content = (
            f"Azerbaijan State Programme (Dövlət Proqramı) {year} catalogue: the state funds {level_label} study "
            f"at {university} ({country}) in {len(programmes)} programme(s): " + "; ".join(programmes) + ". "
            "Being on this list means the programme is eligible for state funding; it is not an admission or an award."
        )
        docs.append({
            "content": content,
            "metadata": {
                "origin": ORIGIN, "kind": "state_programme_catalogue", "university": university,
                "country": country, "level": level, "source_url": source_url,
            },
        })
    return docs


async def _embed(texts: List[str]) -> List[List[float]]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=_require_api_key())
    vectors: List[List[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        response = await client.embeddings.create(input=texts[start:start + BATCH_SIZE], model=MODEL)
        vectors.extend(item.embedding for item in sorted(response.data, key=lambda d: d.index))
    return vectors


async def main() -> None:
    if_empty = "--if-empty" in sys.argv
    async with AsyncSessionLocal() as session:
        if if_empty:
            existing_doc = (await session.execute(select(UniversityDocument).limit(1))).scalars().first()
            if existing_doc is not None:
                print("RAG university documents already indexed; skipping.")
                return

        requirements = (await session.execute(select(ProgramRequirement))).scalars().all()
        catalogue = (await session.execute(select(DPCatalogueEntry))).scalars().all()

        docs = [render_requirement(r) for r in requirements]
        docs += [render_scholarship(s) for s in ALL_GLOBAL_SCHOLARSHIPS]
        docs += render_dp_groups(catalogue)

        vectors = await _embed([d["content"] for d in docs])

        await session.execute(
            delete(UniversityDocument).where(UniversityDocument.doc_metadata["origin"].astext == ORIGIN)
        )
        session.add_all(
            UniversityDocument(content=d["content"], embedding=v, doc_metadata=d["metadata"])
            for d, v in zip(docs, vectors)
        )
        await session.commit()

    print(
        f"Indexed {len(docs)} documents: {len(requirements)} requirement rows, "
        f"{len(ALL_GLOBAL_SCHOLARSHIPS)} scholarships, {len(docs) - len(requirements) - len(ALL_GLOBAL_SCHOLARSHIPS)} "
        f"State Programme university lists ({len(catalogue)} catalogue rows)."
    )


if __name__ == "__main__":
    asyncio.run(main())
