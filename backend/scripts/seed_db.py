import asyncio
import datetime
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.program import Program
from app.models.student import Student


async def seed_database():
    """
    Seed script to initialize database tables and populate initial mock data for MVP testing.
    """
    print("Starting database schema initialization and seeding...")

    # 1. Ensure pgvector extension and create all tables
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            print("Verified 'vector' (pgvector) extension in PostgreSQL.")
        except Exception as e:
            print(f"Notice: Vector extension check skipped or requires superuser: {e}")

        # Ensure email and hashed_password columns exist on existing students table
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS email VARCHAR(255);"))
            await conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);"))
        except Exception as e:
            print(f"Notice: Column alter check: {e}")

        await conn.run_sync(Base.metadata.create_all)
        print("Successfully created/verified all database tables.")

    # 2. Inject initial mock records using AsyncSession
    async with AsyncSessionLocal() as session:
        # Check if programs already seeded
        existing_programs = await session.execute(text("SELECT COUNT(*) FROM programs;"))
        program_count = existing_programs.scalar()

        if program_count == 0:
            mock_programs = [
                Program(
                    university_name="Technical University of Munich (TU Munich)",
                    program_name="MSc Computer Science",
                    degree_level="master",
                    field="Computer Science",
                    country="Germany",
                    min_gpa=3.2,
                    min_ielts=6.5,
                    min_toefl=88,
                    tuition_fee=12000.0,
                    currency="EUR",
                    deadline=datetime.date(2026, 11, 30),
                    requirements_text="Bachelor degree in CS or related quantitative discipline. IELTS 6.5 minimum.",
                    source_url="https://www.tum.de/en/studies/degree-programs/detail/informatics-master-of-science-msc",
                    is_active=True
                ),
                Program(
                    university_name="University College London (UCL)",
                    program_name="BSc Data Science",
                    degree_level="bachelor",
                    field="Data Science",
                    country="United Kingdom",
                    min_gpa=3.5,
                    min_ielts=7.0,
                    min_toefl=100,
                    tuition_fee=25000.0,
                    currency="GBP",
                    deadline=datetime.date(2026, 1, 15),
                    requirements_text="High school diploma with Mathematics A-level or equivalent. IELTS 7.0 minimum.",
                    source_url="https://www.ucl.ac.uk/prospective-students/undergraduate/degrees/data-science-bsc",
                    is_active=True
                ),
                Program(
                    university_name="University of Amsterdam (UvA)",
                    program_name="MSc Artificial Intelligence",
                    degree_level="master",
                    field="Artificial Intelligence",
                    country="Netherlands",
                    min_gpa=3.3,
                    min_ielts=6.5,
                    min_toefl=92,
                    tuition_fee=15000.0,
                    currency="EUR",
                    deadline=datetime.date(2026, 12, 1),
                    requirements_text="Strong foundation in Linear Algebra, Probability, and Python programming.",
                    source_url="https://www.uva.nl/en/programmes/masters/artificial-intelligence/artificial-intelligence.html",
                    is_active=True
                )
            ]
            session.add_all(mock_programs)
            print("Injected 3 mock university programs (TU Munich, UCL, UvA).")

        # Check if student profile already seeded
        existing_student = await session.execute(text("SELECT * FROM students WHERE email = 'student@ausa.edu.az';"))
        student = existing_student.first()

        if not student:
            mock_pwd_hash = get_password_hash("password123")
            mock_student = Student(
                email="student@ausa.edu.az",
                hashed_password=mock_pwd_hash,
                gpa=3.60,
                ielts=7.0,
                toefl=98,
                degree_level="master",
                field_of_study="Computer Science",
                country="Azerbaijan",
                research_experience=True,
                projects="Built machine learning pipeline for automated academic transcript parsing.",
                budget="18000",
                goals="Pursue Master's degree in CS in Western Europe with full or partial scholarship support."
            )
            session.add(mock_student)
            print("Injected default student profile (student@ausa.edu.az / password123).")

        await session.commit()
        print("Successfully committed database seeding transactions!")


if __name__ == "__main__":
    asyncio.run(seed_database())
