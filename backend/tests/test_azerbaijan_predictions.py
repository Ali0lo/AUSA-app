"""Tests for the Azerbaijan cutoff prediction listing filters."""
import pandas as pd

from app.services.prediction.azerbaijan import AzerbaijanPredictionService


def _service(rows):
    raw = pd.DataFrame(rows)
    raw["program_key"] = raw["source_program_code"].astype(str)
    return AzerbaijanPredictionService(raw=raw, prepared=None, artifact=None, metrics={})


def _row(code, university):
    return {
        "source_program_code": code, "university_name": university, "department_name": "Informatika",
        "score_type": "I qrup", "intake_year": 2025, "cutoff_value": 600.0,
    }


def test_university_filter_matching_an_abbreviation_exactly_does_not_pull_in_longer_ones():
    # The page's "ADA University" option sends "ada"; a substring match also returned ADAU,
    # the Agrarian University, mixing its programmes into ADA's.
    service = _service([_row("ada-1", "ADA"), _row("adau-1", "ADAU")])

    names = {p["university_name"] for p in service.list_predictions(university="ada")}

    assert names == {"ADA"}


def test_university_filter_still_matches_part_of_a_name_when_nothing_matches_exactly():
    service = _service([_row("ada-1", "ADA"), _row("adau-1", "ADAU")])

    names = {p["university_name"] for p in service.list_predictions(university="AD")}

    assert names == {"ADA", "ADAU"}
