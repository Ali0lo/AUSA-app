"""
Automated Database Seeding Script for AUSA Platform.
Populates baseline universities, programs, scholarships, vector document chunks, and sample student profiles.
Uses OpenAI text-embedding-3-small vectors for accurate RAG similarity search.
Designed for idempotent execution on fresh installs or live demonstration setups.
"""

import asyncio
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

# Ensure backend root directory is in sys.path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.document import UniversityDocument
from app.models.program import Program
from app.models.scholarship import Scholarship
from app.models.student import Student
from app.services.embeddings import get_embedding_async


# Baseline Data Fixtures
PROGRAM_FIXTURES: List[Dict[str, Any]] = [
    {
        "id": 101,
        "university_name": "ADA University",
        "program_name": "B.S. Computer Science",
        "degree_level": "bachelor",
        "field": "Computer Science",
        "country": "Azerbaijan",
        "min_gpa": 3.0,
        "min_ielts": 6.0,
        "min_toefl": 75,
        "tuition_fee": 3820.0,
        "currency": "USD",
        "requirements_text": "DIM/TQDK Entrance Exam minimum score requirement: 600 / 700 points. IELTS 6.0 or TOEFL 75 required.",
        "source_url": "https://ada.edu.az/en/admissions/bachelor/computer-science",
        "confidence_score": 95.0,
        "verification_status": "verified",
        "verified_by": "admin@ausa.edu.az",
    },
    {
        "id": 102,
        "university_name": "ADA University",
        "program_name": "M.S. Data Analytics",
        "degree_level": "master",
        "field": "Data Science",
        "country": "Azerbaijan",
        "min_gpa": 3.2,
        "min_ielts": 6.5,
        "min_toefl": 80,
        "tuition_fee": 4410.0,
        "currency": "USD",
        "requirements_text": "Bachelor degree in quantitative field. IELTS 6.5 or TOEFL 80.",
        "source_url": "https://ada.edu.az/en/admissions/master/data-analytics",
        "confidence_score": 92.0,
        "verification_status": "verified",
        "verified_by": "admin@ausa.edu.az",
    },
    {
        "id": 103,
        "university_name": "UNEC (Azerbaijan State University of Economics)",
        "program_name": "B.S. Information Security",
        "degree_level": "bachelor",
        "field": "Cybersecurity",
        "country": "Azerbaijan",
        "min_gpa": 2.8,
        "min_ielts": 5.5,
        "tuition_fee": 2060.0,
        "currency": "USD",
        "requirements_text": "DIM Entrance Exam Group 1 requirement: 580 / 700 points.",
        "source_url": "https://unec.edu.az/en/admissions/undergraduate/information-security",
        "confidence_score": 90.0,
        "verification_status": "verified",
        "verified_by": "admin@ausa.edu.az",
    },
    {
        "id": 104,
        "university_name": "Baku Higher Oil School (BANM / BHOS)",
        "program_name": "B.S. Software Engineering",
        "degree_level": "bachelor",
        "field": "Software Engineering",
        "country": "Azerbaijan",
        "min_gpa": 3.5,
        "min_ielts": 6.5,
        "tuition_fee": 2650.0,
        "currency": "USD",
        "requirements_text": "DIM Entrance Exam Group 1 score: 650+ / 700 points. High proficiency in Math and Physics.",
        "source_url": "https://bhos.edu.az/en/programmes/software-engineering",
        "confidence_score": 96.0,
        "verification_status": "verified",
        "verified_by": "admin@ausa.edu.az",
    },
    {
        "id": 105,
        "university_name": "Technical University of Munich (TUM)",
        "program_name": "M.Sc. Informatics",
        "degree_level": "master",
        "field": "Computer Science",
        "country": "Germany",
        "min_gpa": 3.2,
        "min_ielts": 7.0,
        "min_toefl": 88,
        "tuition_fee": 0.0,
        "currency": "EUR",
        "requirements_text": "Tuition €0. Blocked Bank Account minimum €11,208 per year for visa. IELTS 7.0 or TOEFL 88 required.",
        "source_url": "https://www.tum.de/en/studies/degree-programs/detail/informatics-master-of-science-msc",
        "confidence_score": 98.0,
        "verification_status": "verified",
        "verified_by": "admin@ausa.edu.az",
    },
    {
        "id": 106,
        "university_name": "RWTH Aachen University",
        "program_name": "M.Sc. Mechanical Engineering",
        "degree_level": "master",
        "field": "Engineering",
        "country": "Germany",
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "tuition_fee": 0.0,
        "currency": "EUR",
        "requirements_text": "Tuition €0. Blocked Account minimum €11,208. Non-EU bachelor applicants require Studienkolleg preparatory certificate.",
        "source_url": "https://www.rwth-aachen.de/go/id/bkh",
        "confidence_score": 94.0,
        "verification_status": "verified",
        "verified_by": "admin@ausa.edu.az",
    },
    {
        "id": 107,
        "university_name": "Heidelberg University",
        "program_name": "B.Sc. Computer Science",
        "degree_level": "bachelor",
        "field": "Computer Science",
        "country": "Germany",
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "tuition_fee": 3250.0,
        "currency": "USD",
        "requirements_text": "Non-EU tuition €1,500/semester. TestDaF TDN 4 / Goethe C1 required for German instruction track.",
        "source_url": "https://www.uni-heidelberg.de/en/study/all-subjects/computer-science",
        "confidence_score": 91.0,
        "verification_status": "verified",
        "verified_by": "admin@ausa.edu.az",
    },
]

SCHOLARSHIP_FIXTURES: List[Dict[str, Any]] = [
    {
        "id": 201,
        "name": "DAAD Master Studies Scholarship for All Academic Disciplines",
        "provider": "German Academic Exchange Service (DAAD)",
        "country": "Germany",
        "degree_level": "master",
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "amount": "100% Tuition Waiver + €934/month living stipend + €11,208 visa guarantee + travel allowance",
        "eligibility_text": "Open to international graduates with a Bachelor degree. Requires strong academic record and motivation letter.",
        "source_url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
    },
    {
        "id": 202,
        "name": "State Program on Education of Youth in Prestigious Foreign Higher Education Institutions (2022–2026)",
        "provider": "Ministry of Science and Education of the Republic of Azerbaijan",
        "country": "Azerbaijan",
        "degree_level": "master",
        "min_gpa": 3.2,
        "min_ielts": 6.5,
        "amount": "Full-Ride: 100% Tuition + monthly living stipend + health insurance + round-trip flights",
        "eligibility_text": "Azerbaijani citizens admitted to top target global universities (QS Top 200).",
        "source_url": "https://dp.edu.az/az",
    },
    {
        "id": 203,
        "name": "ADA University Merit Scholarship for Top Scorers",
        "provider": "ADA University",
        "country": "Azerbaijan",
        "degree_level": "bachelor",
        "min_gpa": 3.5,
        "min_ielts": 6.0,
        "amount": "50% to 100% Tuition Waiver based on DIM Entrance Exam percentile",
        "eligibility_text": "Students scoring 650+ points on the state DIM (TQDK) entrance exam.",
        "source_url": "https://ada.edu.az/en/admissions/scholarships",
    },
]

DOCUMENT_FIXTURES: List[Dict[str, Any]] = [
    {
        "id": 301,
        "university_id": 101,
        "program_id": 101,
        "content": (
            "ADA University Bachelor of Science in Computer Science admissions guidelines: "
            "Requires minimum DIM/TQDK score of 600 out of 700 points. Language proficiency: IELTS 6.0 or TOEFL 75. "
            "Annual tuition fee is 6,500 AZN (~$3,820 USD). Merit scholarships cover up to 100% tuition for scores above 650."
        ),
        "doc_metadata": {"university": "ADA University", "country": "Azerbaijan", "program_id": 101},
    },
    {
        "id": 302,
        "university_id": 105,
        "program_id": 105,
        "content": (
            "Technical University of Munich (TUM) Master of Science in Informatics guidelines: "
            "Tuition is €0 per year for public master programs. Student visa requires proof of financial resources "
            "via Blocked Bank Account (Sperrkonto) containing minimum €11,208 EUR per year. IELTS 7.0 or TOEFL 88 required."
        ),
        "doc_metadata": {"university": "TU Munich", "country": "Germany", "program_id": 105},
    },
    {
        "id": 303,
        "university_id": 106,
        "program_id": 106,
        "content": (
            "RWTH Aachen University M.Sc. Mechanical Engineering admissions guidelines: "
            "No tuition fee charged. Financial proof requirement: €11,208 EUR blocked account. "
            "Non-EU secondary school diplomas require Studienkolleg preparatory course and Feststellungsprüfung (FSP)."
        ),
        "doc_metadata": {"university": "RWTH Aachen", "country": "Germany", "program_id": 106},
    },
    {
        "id": 304,
        "university_id": None,
        "program_id": None,
        "content": (
            "DAAD (German Academic Exchange Service) Master Studies Scholarship guidelines: "
            "Provides full scholarship coverage including 100% tuition waiver, €934 per month living stipend, "
            "health insurance, and €11,208 visa financial guarantee. Open to international applicants with a Bachelor degree."
        ),
        "doc_metadata": {"scholarship": "DAAD", "country": "Germany"},
    },
    {
        "id": 305,
        "university_id": None,
        "program_id": None,
        "content": (
            "State Program on Education of Youth in Prestigious Foreign Higher Education Institutions (2022–2026): "
            "Fully funded Azerbaijani government state scholarship for master and PhD studies at top global QS Top 200 universities. "
            "Covers 100% tuition, monthly stipend, health insurance, and round-trip flights."
        ),
        "doc_metadata": {"scholarship": "State Program", "country": "Azerbaijan"},
    },
]


async def seed_database(session: AsyncSession) -> Dict[str, Any]:
    """
    Idempotently populate database with baseline universities, programs, scholarships, and OpenAI vector document chunks.
    
    Args:
        session: Active SQLAlchemy AsyncSession.
        
    Returns:
        Summary dictionary containing counts of seeded items.
    """
    # 1. Seed Programs (Upsert / Replace by ID)
    seeded_programs_count = 0
    for prog_data in PROGRAM_FIXTURES:
        stmt = select(Program).where(Program.id == prog_data["id"])
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing is not None:
            for k, v in prog_data.items():
                setattr(existing, k, v)
        else:
            new_prog = Program(**prog_data)
            session.add(new_prog)
        seeded_programs_count += 1

    # 2. Seed Scholarships (Upsert / Replace by ID)
    seeded_scholarships_count = 0
    for sch_data in SCHOLARSHIP_FIXTURES:
        stmt = select(Scholarship).where(Scholarship.id == sch_data["id"])
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing is not None:
            for k, v in sch_data.items():
                setattr(existing, k, v)
        else:
            new_sch = Scholarship(**sch_data)
            session.add(new_sch)
        seeded_scholarships_count += 1

    # 3. Seed Vector Documents with OpenAI Embeddings
    seeded_docs_count = 0
    for doc_data in DOCUMENT_FIXTURES:
        # Generate real OpenAI vector embedding for document chunk
        vector_embedding = await get_embedding_async(doc_data["content"])

        doc_payload = {
            "id": doc_data["id"],
            "university_id": doc_data["university_id"],
            "program_id": doc_data["program_id"],
            "content": doc_data["content"],
            "embedding": vector_embedding,
            "doc_metadata": doc_data["doc_metadata"],
        }

        stmt = select(UniversityDocument).where(UniversityDocument.id == doc_payload["id"])
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing is not None:
            for k, v in doc_payload.items():
                setattr(existing, k, v)
        else:
            new_doc = UniversityDocument(**doc_payload)
            session.add(new_doc)
        seeded_docs_count += 1

    # 4. Seed Demo Student Account if not exists
    stmt = select(Student).where(Student.email == "std_demo@ausa.edu.az")
    res = await session.execute(stmt)
    existing_student = res.scalar_one_or_none()
    if existing_student is None:
        demo_student = Student(
            email="std_demo@ausa.edu.az",
            hashed_password="mock_hashed_password_2026",
            gpa=3.6,
            ielts=7.0,
            degree_level="master",
            field_of_study="Computer Science",
            country="Azerbaijan",
            budget="18000"
        )
        session.add(demo_student)

    await session.commit()

    return {
        "status": "success",
        "programs_seeded": seeded_programs_count,
        "scholarships_seeded": seeded_scholarships_count,
        "documents_seeded": seeded_docs_count,
        "message": "Database successfully populated with baseline university, scholarship, and OpenAI vector embeddings."
    }


async def main():
    """CLI execution entrypoint for database seeding script."""
    print("[AUSA Database Seeder] Connecting to database...")
    async with AsyncSessionLocal() as session:
        try:
            summary = await seed_database(session)
            print(f"✓ Seeding complete!")
            print(f"  - Programs: {summary['programs_seeded']}")
            print(f"  - Scholarships: {summary['scholarships_seeded']}")
            print(f"  - Vector Chunks: {summary['documents_seeded']}")
        except Exception as e:
            print(f"✗ Database seeding failed: {e}")
            await session.rollback()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
