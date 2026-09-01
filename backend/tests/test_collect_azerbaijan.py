"""Tests for collect_azerbaijan.py's variant-suffixing invariant.

Ruling 14: the unique index on program_cutoff_history(country, source_program_code,
intake_year) depends entirely on this collector suffixing every variant row's
source_program_code with --vN whenever sec.az publishes more than one row for the
same (specialty, university, group). This test guards that invariant at the layer
that actually holds it -- a database-level test could pass "because the rows happen
to differ" without ever exercising the code responsible for making them differ.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))
from collect_azerbaijan import parse_list_page  # noqa: E402

HEADER_ROW = (
    "<tr><th>İxtisas</th><th>Universitet</th><th>2023</th><th>2024</th>"
    "<th>2025</th><th>Trend</th></tr>"
)


def _table(rows: str) -> str:
    return f'<table class="k-table"><thead>{HEADER_ROW}</thead><tbody>{rows}</tbody></table>'


def _row(specialty: str, university: str, group: str, y2023: str, y2024: str, y2025: str) -> str:
    return (
        f'<tr data-group="{group}"><td>{specialty}</td><td>{university}</td>'
        f"<td>{y2023}</td><td>{y2024}</td><td>{y2025}</td><td>—</td></tr>"
    )


# Three rows sec.az publishes as byte-identical apart from their scores: same specialty,
# same university, same group. This is the exact shape that produced the ambiguous
# variants documented in parse_list_page (the eyani/qiyabi and language-section rows).
THREE_IDENTICAL_ROWS = _table(
    _row("Kompüter elmləri", "ADA", "1", "600", "610", "620")
    + _row("Kompüter elmləri", "ADA", "1", "580", "590", "600")
    + _row("Kompüter elmləri", "ADA", "1", "560", "570", "580")
)


def test_every_variant_row_gets_a_distinct_suffixed_code():
    """Each of the 3 identical (specialty, university, group) rows must end up with its
    own --vN-suffixed source_program_code, so no two rows collide on
    (country, source_program_code, intake_year) -- the key the database now enforces.
    """
    df = parse_list_page(THREE_IDENTICAL_ROWS)

    codes = set(df["source_program_code"])
    assert len(codes) == 3, f"expected 3 distinct variant codes, got {codes}"
    assert all(code.startswith("komputer-elmleri--ada--g1--v") for code in codes)
    assert {code.rsplit("--v", 1)[1] for code in codes} == {"1", "2", "3"}

    duplicates = df.duplicated(["source_program_code", "intake_year"]).sum()
    assert duplicates == 0, "no two rows may share (source_program_code, intake_year)"


def test_a_single_unambiguous_row_is_not_suffixed():
    """Only rows that actually collide get a --vN suffix; a lone row keeps its bare code."""
    df = parse_list_page(_table(_row("Kompüter elmləri", "ADA", "1", "600", "610", "620")))

    codes = set(df["source_program_code"])
    assert codes == {"komputer-elmleri--ada--g1"}
