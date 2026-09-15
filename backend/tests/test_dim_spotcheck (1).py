"""Sampling must be reproducible without inventing a DİM verification."""
import csv
import pytest
from scripts.prepare_dim_spotcheck import prepare


def test_missing_dataset_does_not_create_a_false_review(tmp_path):
    output=tmp_path/'review.csv'
    with pytest.raises(FileNotFoundError, match='unavailable'):
        prepare(tmp_path/'missing.csv',output)
    assert not output.exists()


def test_sample_is_reproducible_and_keeps_review_fields_empty(tmp_path):
    source=tmp_path/'cutoffs.csv'
    with source.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['source_program_code','intake_year','cutoff_value','university_name'])
        w.writeheader()
        w.writerows(dict(source_program_code=str(i),intake_year=2025,cutoff_value=500+i,university_name='Fixture') for i in range(40))
    a,b=tmp_path/'review-a.csv',tmp_path/'review-b.csv'
    stats=prepare(source,a)
    prepare(source,b)
    assert a.read_bytes()==b.read_bytes()
    assert stats['sampled']==30 and stats['checked']==0
    with a.open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    assert len({r['source_program_code'] for r in rows})==30
    assert all(not r['reviewer'] and not r['comparison'] and not r['dim_value'] for r in rows)
    with pytest.raises(ValueError,match='overwrite'):
        prepare(source,source)
