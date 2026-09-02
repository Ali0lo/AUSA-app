"""AUSA Models Package."""
from app.models.application import StudentApplication
from app.models.cutoff_history import ProgramCutoffHistory
from app.models.document import UniversityDocument
from app.models.dp_catalogue import DPCatalogueEntry
from app.models.program import Program
from app.models.qualifications import ProgramRequirement, StudentQualification
from app.models.scholarship import Scholarship
from app.models.student import Student

__all__ = [
    "StudentApplication",
    "ProgramCutoffHistory",
    "UniversityDocument",
    "DPCatalogueEntry",
    "Program",
    "ProgramRequirement",
    "StudentQualification",
    "Scholarship",
    "Student",
]
