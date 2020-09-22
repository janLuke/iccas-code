"""
Download new reports and make all datasets, skipping existing ones.
"""
from pathlib import Path
from typing import (
    List,
    Tuple
)

import pandas as pd

from settings import (
    FULL_DATASET_DIR,
    ISS_REPORTS_DIR,
    DATA_BY_DATE_DIR,
    get_date_from_filename,
    get_full_dataset_path,
    get_single_date_dataset_path
)
from table_extraction.common import (
    TableExtractor,
    recompute_derived_columns
)
from table_extraction.pypdf_extractor import PyPDFTableExtractor


def make_single_date_datasets(reports_dir: Path = ISS_REPORTS_DIR,
                              data_dir: Path = DATA_BY_DATE_DIR,
                              table_extractor: TableExtractor = PyPDFTableExtractor(),
                              skip_existing=True) -> List[Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    new_dataset_paths = []
    relative_paths = sorted(reports_dir.iterdir())
    for relpath in relative_paths:
        path = reports_dir / relpath
        date = relpath.stem
        out_path = get_single_date_dataset_path(date, dirpath=data_dir)
        print('-' * 80)
        if skip_existing and out_path.exists():
            print(f'Dataset for report of {date} already exists')
        else:
            print(f"Making dataset for report of {date} ...")
            table = table_extractor(path, date)
            table = recompute_derived_columns(table)
            table.to_csv(out_path, index=False)
            new_dataset_paths.append(out_path)
            print('Saved to', out_path)

    print('\nNew datasets written:', new_dataset_paths, end='\n\n')
    return new_dataset_paths


def list_datasets_by_date(dirpath: Path) -> List[Tuple[str, Path]]:
    date_path = [(get_date_from_filename(path.name), path)
                 for path in dirpath.iterdir()]
    return sorted(date_path, key=lambda p: p[0])


def make_full_dataset(input_dir=DATA_BY_DATE_DIR,
                      output_dir=FULL_DATASET_DIR):
    date_path_pairs = list_datasets_by_date(input_dir)
    if not date_path_pairs:
        print('No datasets found in', input_dir)
        return False

    out_path = get_full_dataset_path(dirpath=output_dir)
    iccas_by_date = {}
    for date, path in date_path_pairs:
        iccas_by_date[date] = pd.read_csv(path, index_col='age_group')

    full = pd.concat(iccas_by_date.values(), axis=0,
                     keys=iccas_by_date.keys(), names=['date', 'age_group'])

    output_dir.mkdir(parents=True, exist_ok=True)
    full.to_csv(out_path)
    print('Full dataset written to', out_path)
    return out_path


if __name__ == '__main__':
    from download_reports import download_missing_reports

    download_missing_reports()
    make_single_date_datasets()
    make_full_dataset()
