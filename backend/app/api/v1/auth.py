from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.domain.grades import KNOWN_SCALE_KEYS, resolve_scale
from app.models.student import Student
from app.schemas.common import DegreeLevel

router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])


class LoginRequest(BaseModel):
    """Payload for student login."""
    email: str = Field(..., description="Student email address")
    password: str = Field(..., description="Plaintext password")


class TokenResponse(BaseModel):
    """JWT Token Response."""
    access_token: str = Field(..., description="Signed JWT Access Token")
    token_type: str = Field(default="bearer", description="Token type")


class RegisterRequest(BaseModel):
    """Payload for student registration.

    Every academic/profile field is optional and defaults to None, not a plausible
    number. A student who registers with only an email and a password has not told us
    their GPA, budget, IELTS/TOEFL, degree level, field of study, or country -- and
    those values are persisted, so an invented default here would be indistinguishable
    from data the student entered, forever (unlike a read-time substitution, which
    disappears when removed). Previously defaulted to gpa=3.5, budget=15000,
    ielts=7.0, toefl=95, degree_level="master", field_of_study="Computer Science",
    country="Azerbaijan", and wrote every one of those into the database (ADR-0004).
    """
    email: str = Field(..., description="Student email address")
    password: str = Field(..., description="Password (min 6 characters)")
    # No `le=4.0`. That bound was an assumption about which country the student went to
    # school in, and it rejected the grade our own users hold: an Azerbaijani attestat
    # average is out of 5, so a real 4.5 was refused as invalid at registration. The scale
    # is what decides the valid range, so it is validated against `gpa_scale` below rather
    # than against a hardcoded ceiling. Same rule `/routes/assess` already follows.
    gpa: Optional[float] = Field(default=None, ge=0.0)
    gpa_scale: Optional[str] = Field(
        default=None,
        description=f"Which scale the grade is on. One of: {', '.join(KNOWN_SCALE_KEYS)}. "
                    f"Required whenever a grade is given -- a grade without its scale is "
                    f"not a number.",
    )
    budget: Optional[float] = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def grade_and_scale_travel_together(self) -> "RegisterRequest":
        """A grade with no scale, and a scale with no grade, are both rejected.

        Storing 4.5 with no scale would leave a row nobody can interpret later: is it an
        excellent attestat or an impossible US GPA? And a value outside its own scale's
        range is a typo or the wrong scale picked, which is worth saying now rather than
        letting it silently fail every comparison downstream.
        """
        if self.gpa is not None and self.gpa_scale is None:
            raise ValueError(
                "gpa_scale is required when gpa is given. A grade without its scale cannot "
                f"be compared to anything. One of: {', '.join(KNOWN_SCALE_KEYS)}."
            )
        if self.gpa_scale is not None:
            scale = resolve_scale(self.gpa_scale)
            if scale is None:
                raise ValueError(
                    f"gpa_scale {self.gpa_scale!r} is not a scale we know. "
                    f"One of: {', '.join(KNOWN_SCALE_KEYS)}."
                )
            if self.gpa is None:
                raise ValueError("gpa_scale was given without a gpa.")
            if not scale.floor <= self.gpa <= scale.ceiling:
                raise ValueError(
                    f"gpa {self.gpa} is outside the {scale.key} scale "
                    f"({scale.floor}-{scale.ceiling}): {scale.description}."
                )
        return self
    ielts: Optional[float] = Field(default=None, ge=0.0, le=9.0)
    toefl: Optional[int] = Field(default=None, ge=0, le=120)
    degree_level: Optional[DegreeLevel] = Field(default=None)
    field_of_study: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)


class StudentUserResponse(BaseModel):
    """User response model returned by GET /auth/me.

    Every profile field is optional because every corresponding column is nullable.
    A student who has not entered a GPA has no GPA -- returning a stand-in 3.5 would
    put a number the student never gave us into their eligibility checks.
    """
    id: int
    email: Optional[str] = None
    gpa: Optional[float] = None
    # Always sent beside the grade. A client that renders 4.5 without knowing it is out of
    # 5 will draw it against a 4.0 bar and show the student a failure they do not have.
    gpa_scale: Optional[str] = None
    budget: Optional[float] = None
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    degree_level: Optional[DegreeLevel] = None
    field_of_study: Optional[str] = None
    country: Optional[str] = None


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Student JWT Login",
    description="Authenticate student credentials and return a signed JWT access token."
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Verify password credentials and return JWT access token."""
    try:
        stmt = select(Student).where(Student.email == payload.email)
        result = await db.execute(stmt)
        student = result.scalars().first()

        if not student or not student.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(payload.password, student.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(subject=student.id)
        return TokenResponse(access_token=token, token_type="bearer")
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        # Never issue a token when credentials could not be checked. This previously
        # returned a valid token for student 101 on any database error -- an
        # authentication bypass triggered by an outage, not a dev convenience.
        # See docs/adr/0004 -- no silent fallbacks.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login is temporarily unavailable.",
        ) from exc


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Student Registration",
    description="Register a new student profile and return an initial JWT access token."
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Register student account."""
    try:
        stmt = select(Student).where(Student.email == payload.email)
        result = await db.execute(stmt)
        existing = result.scalars().first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student with this email already exists."
            )

        hashed_pwd = get_password_hash(payload.password)
        student = Student(
            email=payload.email,
            hashed_password=hashed_pwd,
            gpa=payload.gpa,
            gpa_scale=payload.gpa_scale,
            budget=str(payload.budget) if payload.budget is not None else None,
            ielts=payload.ielts,
            toefl=payload.toefl,
            degree_level=payload.degree_level,
            field_of_study=payload.field_of_study,
            country=payload.country,
        )
        db.add(student)
        await db.commit()
        await db.refresh(student)

        token = create_access_token(subject=student.id)
        return TokenResponse(access_token=token, token_type="bearer")
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        # No account was created, so no token is owed. This previously returned a valid
        # token for student 101 whenever the write failed. See docs/adr/0004 -- no
        # silent fallbacks.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration is temporarily unavailable.",
        ) from exc


@router.get(
    "/me",
    response_model=StudentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Student Profile",
    description="Retrieve the authenticated student profile matching the Bearer JWT token."
)
async def get_me(
    current_student: Student = Depends(get_current_user)
) -> StudentUserResponse:
    """Get authenticated student info. Unset fields are returned as null, not filled in."""
    budget_val: Optional[float] = None
    if current_student.budget:
        try:
            budget_val = float(current_student.budget)
        except ValueError:
            budget_val = None

    degree_val: Optional[DegreeLevel] = None
    if current_student.degree_level in ["bachelor", "master", "phd"]:
        degree_val = current_student.degree_level  # type: ignore

    return StudentUserResponse(
        id=current_student.id,
        email=current_student.email,
        gpa=current_student.gpa,
        gpa_scale=current_student.gpa_scale,
        budget=budget_val,
        ielts=current_student.ielts,
        toefl=current_student.toefl,
        degree_level=degree_val,
        field_of_study=current_student.field_of_study,
        country=current_student.country,
    )
