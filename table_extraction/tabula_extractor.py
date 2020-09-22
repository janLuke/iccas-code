"""
Table extractor based on Tabula. Not used anymore,
but I'm leaving it here, just in case.
"""
import json
from bisect import bisect
from pathlib import Path
from typing import (
    Optional,
    Tuple
)

import pandas as pd
import tabula

from table_extraction.common import (
    TableExtractor,
    find_table_page,
    TableExtractionError,
    COLUMNS,
    CONVERTER_BY_COLUMN,
    cartesian_join,
    COLUMN_PREFIXES,
    normalize_table,
    sanity_check_with_totals
)


def _load_tabula_templates(dirpath):
    """
    Returns a dictionary of tabula templates by date of first validity.

    Tabula templates are JSON files used to describe the location of the table
    inside a pdf report, i.e. the page and the selection area inside the page.
    This script ignores the page, since it is automatically detected and make
    use only of the selection area.

    Tabula templates are generated with the Tabula app and saved in a sub-folder
    of the project with name "{date}.tabula-template.json" where {date} is the
    date of first validity of the template.
    """
    by_date = {}
    for relpath in dirpath.iterdir():
        date = relpath.name.split('.', 1)[0]
        with open(Path(dirpath, relpath)) as f:
            by_date[date] = json.load(f)[0]
    return by_date


def _tabula_template_getter(template_dir):
    template_by_date = _load_tabula_templates(template_dir)
    dates = sorted(template_by_date.keys())  # dates of first validity of the templates

    def get_tabula_template(report_date):
        """ Returns the tabula template to use given the report date """
        i = bisect(dates, report_date)  # index of 1st date >= report_date
        template_date = dates[i - 1]
        return template_by_date[template_date]

    return get_tabula_template


def _area_from_template(template):
    return template['y1'], template['x1'], template['y2'], template['x2']


def extract_table(pdf_path,
                  area: Tuple[float, float, float, float],
                  page_number: Optional[int] = None) -> pd.DataFrame:
    """ Returns the table in a pd.DataFrame """
    if page_number is None:
        _, page_number = find_table_page(pdf_path)

    tables = tabula.read_pdf(
        str(pdf_path), pages=page_number, area=area, multiple_tables=False,
        pandas_options={'names': COLUMNS, 'converters': CONVERTER_BY_COLUMN})
    if not tables:
        raise TableExtractionError('tabula.read_pdf did not return anything')

    raw_df = tables[0]

    if len(raw_df) == 12:
        pass
    elif (
        # In report of 2020-03-2020 the age_group "Non nota" (unknown) is "Età non nota"
        # and is written in 2 lines; this confounds tabula, which sees 3 rows instead of 1.
        len(raw_df) == 14
        and raw_df.iloc[10, 0].strip().lower() == 'età non'  # row of NaNs
        and raw_df.iloc[11, 0].strip() == ''  # row containing values
        and raw_df.iloc[12, 0].strip().lower() == 'nota'  # row of NaNs
    ):
        raw_df.iloc[10, :] = raw_df.iloc[11, :]
        raw_df.drop(index=[11, 12], inplace=True)
        # int columns are float because of NaNs in this case; let's convert them to int
        int_columns = cartesian_join(COLUMN_PREFIXES, ['cases', 'deaths'])
        raw_df = raw_df.astype({col: int for col in int_columns})
    else:
        raise TableExtractionError(
            'unexpected table length: %d. Expected: %d\n'
            'Age groups: %s' % (len(raw_df.age_group), 12, list(raw_df.age_group)))

    totals = raw_df.iloc[11]
    table = raw_df.iloc[:11].copy()  # remove totals
    normalize_table(table)
    sanity_check_with_totals(table, totals)
    return table


class TabulaTableExtractor(TableExtractor):

    def __init__(self, template_dir):
        self._get_template_by_date = _tabula_template_getter(template_dir)

    def extract(self, path, report_date: str) -> pd.DataFrame:
        template = self._get_template_by_date(report_date)
        area = _area_from_template(template)
        return extract_table(path, area)
