"""Database-backed catalogue browsing and authenticated review of its actual rows."""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin import require_admin_user
from app.api.v1.routes import AssessRoutesPayload, UniversityResponse, _university_response
from app.core.database import get_db
from app.domain.routes import StudentRouteProfile
from app.models.qualifications import ProgramRequirement
from app.models.student import Student
from app.services.catalogue_evidence import content_fingerprint
from app.services.university_requirements import _latest_intake_only, assess_requirement

router = APIRouter(tags=["Catalogue"])


class CatalogueResponse(BaseModel):
    status: str
    total: int
    items: list[UniversityResponse]


async def read_catalogue(db, level, university=None, country=None):
    stmt = select(ProgramRequirement).where(ProgramRequirement.level == level)
    if university:
        stmt = stmt.where(ProgramRequirement.university_name == university)
    if country:
        stmt = stmt.where(ProgramRequirement.country_code == country)
    try:
        return _latest_intake_only(list((await db.execute(stmt)).scalars().all()))
    except SQLAlchemyError as exc:
        raise HTTPException(503, "The catalogue is unavailable. Check database connectivity and migrations.") from exc


@router.get("/catalogue", response_model=CatalogueResponse)
async def catalogue(level: Literal["bachelor", "master"], university: str | None = Query(None, max_length=300),
                    country: str | None = Query(None, pattern="^[A-Z]{2}$"),
                    offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=250),
                    db: AsyncSession = Depends(get_db)):
    rows = await read_catalogue(db, level, university, country)
    return CatalogueResponse(status="listed" if rows else "not_collected", total=len(rows),
                             items=[_university_response(assess_requirement(r)) for r in rows[offset:offset + limit]])


@router.post("/catalogue/assess", response_model=CatalogueResponse)
async def assess_catalogue(payload: AssessRoutesPayload, university: str = Query(..., min_length=1, max_length=300),
                          db: AsyncSession = Depends(get_db)):
    rows = await read_catalogue(db, payload.level_sought, university)
    profile = StudentRouteProfile(**payload.model_dump())
    return CatalogueResponse(status="listed" if rows else "not_collected", total=len(rows),
                             items=[_university_response(assess_requirement(r, profile)) for r in rows])


class ReviewRow(BaseModel):
    revision: str
    requirement: UniversityResponse


@router.get("/admin/catalogue", response_model=list[ReviewRow])
async def review_queue(level: Literal["bachelor", "master"],
                       offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=250),
                       admin: Student = Depends(require_admin_user), db: AsyncSession = Depends(get_db)):
    rows = await read_catalogue(db, level)
    pending = [r for r in rows if r.provenance != "human-verified"]
    return [ReviewRow(revision=content_fingerprint(r), requirement=_university_response(assess_requirement(r)))
            for r in pending[offset:offset + limit]]


class VerifyCataloguePayload(BaseModel):
    revision: str = Field(pattern="^[a-f0-9]{64}$")
    source_checked: Literal[True]


@router.put("/admin/catalogue/{row_id}/verify", response_model=ReviewRow)
async def verify_catalogue(row_id: int, payload: VerifyCataloguePayload,
                           admin: Student = Depends(require_admin_user), db: AsyncSession = Depends(get_db)):
    try:
        # Lock against an import/review changing the row while a human's revision is checked.
        row = (await db.execute(select(ProgramRequirement).where(ProgramRequirement.id == row_id).with_for_update())).scalar_one_or_none()
        if row is None:
            raise HTTPException(404, "No catalogue row with this id.")
        if content_fingerprint(row) != payload.revision:
            raise HTTPException(409, "The requirements changed. Reload and review the current source evidence.")
        if not row.evidence:
            raise HTTPException(422, "Add field-scoped evidence in the curated CSV before verifying this row.")
        row.provenance = "human-verified"
        row.verified_by = admin.email
        row.verified_at = datetime.now(timezone.utc)
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(503, "The catalogue verification could not be saved.") from exc
    return ReviewRow(revision=content_fingerprint(row), requirement=_university_response(assess_requirement(row)))
