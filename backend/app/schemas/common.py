"""Shared scalar types.

`DegreeLevel` used to live in `schemas/matching.py`, next to the weighted-scoring engine
that was deleted. It is not a matching concept -- it is what a student is applying for, and
`auth.py` stores it on the profile -- so it outlives the engine and lives here instead.

Note the mismatch with the route engine, which is deliberate and not yet resolved: this
type still admits `phd`, because existing student rows may carry it, while the route engine
accepts only `bachelor` and `master` (the route-first spec excludes PhD -- supervisor-driven
admission and funded-position financing share no mechanics with the rest). A stored `phd`
profile therefore has no routes to assess, and says so, rather than being silently mapped
to a level it did not choose.
"""
from typing import Literal

DegreeLevel = Literal["bachelor", "master", "phd"]
