"""The README's front-door demo must actually run.

It broke silently once already: `demo_walkthrough.py` created only the DP catalogue table,
and when route plans were joined to `program_requirements` the demo started dying with
`no such table: program_requirements`. Nothing caught it, because nothing ran it -- the
286 tests around it all exercise the endpoint directly and build their own tables.

So this test runs the script the way a person does: as a subprocess, from the repository
root, end to end. It is slower than the rest of the suite (it loads 4,121 catalogue rows)
and that is the price of covering the one artifact a new reader opens first.

It asserts the shape of the output rather than its wording, so a copy edit does not break
it, but a missing section or a crash does.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO = REPO_ROOT / "demo_walkthrough.py"
DP_CSV = REPO_ROOT / "data" / "raw" / "azerbaijan" / "dp-bakalavr-2026.csv"


@pytest.mark.skipif(
    not DP_CSV.exists(),
    reason="DP catalogue CSVs are gitignored; see data/README.md to fetch them",
)
def test_demo_walkthrough_runs_end_to_end():
    result = subprocess.run(
        [sys.executable, str(DEMO)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )

    assert result.returncode == 0, (
        f"demo_walkthrough.py exited {result.returncode}.\n"
        f"--- stdout tail ---\n{result.stdout[-2000:]}\n"
        f"--- stderr tail ---\n{result.stderr[-2000:]}"
    )

    out = result.stdout

    # Every section the README promises. A crash after the catalogue load used to leave the
    # first two of these present and the rest missing, which is why they are checked
    # individually rather than by exit code alone.
    for section in (
        "Seeding the real State Programme catalogue",
        "Where they can actually go",
        "Where they cannot, and the engine says so plainly",
        "Which universities each open plan actually reaches",
        "State Programme funding",
        "What it refuses to say",
    ):
        assert section in out, f"demo output is missing the {section!r} section"

    # The join this test exists to protect: a plan must resolve to named universities, not
    # just to a country. Cambridge is reachable ONLY via the two-hop prep-year path, so its
    # presence proves composition and the requirements join both ran.
    assert "University of Cambridge" in out

    # The product's central finding, which the demo exists to show.
    assert "DE:" in out and "GB:" in out, "both blocked countries should be named"


@pytest.mark.skipif(
    not DP_CSV.exists(),
    reason="DP catalogue CSVs are gitignored; see data/README.md to fetch them",
)
def test_demo_never_prints_an_admission_probability():
    """ADR-0004, checked on the artifact a reader sees rather than only in the API layer."""
    result = subprocess.run(
        [sys.executable, str(DEMO)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert result.returncode == 0

    # The demo names `admission_probability` once, in the closing list of what it refuses to
    # answer, where it is followed by `null`. Any other rendering would be a regression.
    assert "admission_probability" in result.stdout
    assert "%" not in result.stdout.split("admission_probability")[1][:120]
