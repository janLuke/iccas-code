import re
from pathlib import Path

PROJECT_DIR = Path(__file__).parent

ISS_REPORTS_DIR = Path(PROJECT_DIR, 'reports')
ISS_REPORT_FNAME = '{date}.pdf'
ISS_REPORT_MIN_DATE = '2020-03-12'  # the report before this date doesn't contain the data we are looking for
TABULA_TEMPLATES_DIR = Path(PROJECT_DIR, 'tabula-templates')

DATA_REPO = Path(PROJECT_DIR, 'iccas-dataset')
DATA_DIR = Path(DATA_REPO, 'data')
DATA_BY_DATE_DIR = Path(DATA_DIR, 'by-date')
DATE_DATASET_FNAME = 'iccas_{date}'
FULL_DATASET_DIR = DATA_DIR
FULL_DATASET_FNAME = 'iccas_full'

_DATE_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2})')


def get_date_from_filename(fname):
    match = _DATE_PATTERN.search(fname)
    if match is None:
        raise ValueError('filename does not contain a date: ' + fname)
    return match.group(1)


def get_report_path(date, dirpath=ISS_REPORTS_DIR):
    return Path(dirpath, ISS_REPORT_FNAME.format(date=date))


def get_single_date_dataset_path(date, dirpath=DATA_BY_DATE_DIR, ext='.csv'):
    return Path(dirpath, DATE_DATASET_FNAME.format(date=date) + ext)


def get_full_dataset_path(dirpath=FULL_DATASET_DIR, ext='.csv'):
    return Path(dirpath, FULL_DATASET_FNAME + ext)
