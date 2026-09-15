"""Stable content fingerprints for imports and authenticated catalogue review."""
import hashlib
import json
from datetime import date, datetime
from app.models.qualifications import ProgramRequirement

# Reading the same facts again must not erase a person's review. Changing any fact,
# caveat or evidence must. Do not confuse this fingerprint with a source-page hash.
AUDIT_FIELDS = {"id", "retrieved_at", "last_checked", "provenance", "verified_by", "verified_at"}
CONTENT_FIELDS = tuple(c.name for c in ProgramRequirement.__table__.columns if c.name not in AUDIT_FIELDS)


def content_fingerprint(row) -> str:
    def value(field):
        v = row.get(field) if isinstance(row, dict) else getattr(row, field)
        if field == "requirement_scope" and v is None:
            v = "general"
        if isinstance(v, (date, datetime)):
            return v.isoformat()
        return v
    encoded = json.dumps({f: value(f) for f in CONTENT_FIELDS}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
