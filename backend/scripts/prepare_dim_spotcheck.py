"""Prepare a reproducible 30-row DİM review sheet; never claim the review occurred.

python -m scripts.prepare_dim_spotcheck --file ../data/processed/azerbaijan_cutoff_history.csv --output dim_review.csv
Only a reviewer with the actual DİM publication can fill the match and evidence fields.
"""
import argparse
import csv
import hashlib
from pathlib import Path
import random


def prepare(source: Path, output: Path, *, count=30, seed=20260915):
    if not source.is_file():
        raise FileNotFoundError('Cutoff history is unavailable; supply the actual dataset before sampling. No checks have been performed.')
    if source.resolve() == output.resolve():
        raise ValueError('Review output must not overwrite the source dataset')
    with source.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        fields=list(reader.fieldnames or [])
        rows=list(reader)
    required={'source_program_code','intake_year','cutoff_value','university_name'}
    if not required.issubset(fields):
        raise ValueError('Missing cutoff identity/value columns: '+', '.join(sorted(required-set(fields))))
    if count < 1 or len(rows) < count:
        raise ValueError(f'Requested {count} rows from a dataset of {len(rows)}')
    ordered=sorted(enumerate(rows,start=2),key=lambda pair: (pair[1]['source_program_code'],pair[1]['intake_year'],pair[0]))
    sampled=random.Random(seed).sample(ordered,count)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    extra=['source_csv_line','sample_seed','source_sha256','dim_publication_url','dim_page','dim_value','comparison','reviewer','reviewed_at']
    if set(fields)&set(extra):
        raise ValueError('Input is already a review sheet, not a raw cutoff dataset')
    with output.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields+extra)
        writer.writeheader()
        for line,row in sampled:
            writer.writerow({**row,'source_csv_line':line,'sample_seed':seed,'source_sha256':digest})
    return {'sampled':count,'checked':0,'seed':seed,'source_sha256':digest}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--seed',type=int,default=20260915)
    args=parser.parse_args()
    print(prepare(args.file,args.output,seed=args.seed))
