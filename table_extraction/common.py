import abc
import math
import re
from typing import Tuple

import PyPDF3
import numpy
import pandas as pd
from PyPDF3.pdf import PageObject


def to_int(s):
    if not s:
        return math.nan
    return int(s.replace('.', '').replace(' ', ''))


def to_float(s):
    if not s:
        return math.nan
    return float(s.replace(',', '.'))


def cartesian_join(*string_iterables, sep=''):
    from itertools import product
    return (sep.join(iterable) for iterable in product(*string_iterables))


# Useful to find the page containing the table
TABLE_CAPTION_PATTERN = re.compile(
    'TABELLA [0-9- ]+ DISTRIBUZIONE DEI CASI .+ PER FASCIA DI ET. ',
    re.IGNORECASE)

COLUMN_PREFIXES = ('male_', 'female_', '')
COLUMN_FIELDS = ('cases', 'cases_percentage', 'deaths', 'deaths_percentage', 'fatality_rate')
COLUMNS = ('age_group', *cartesian_join(COLUMN_PREFIXES, COLUMN_FIELDS))
COLUMN_CONVERTERS = [str] + [to_int, to_float, to_int, to_float, to_float] * 3  # noqa
CONVERTER_BY_COLUMN = dict(zip(COLUMNS, COLUMN_CONVERTERS))


class TableExtractor(abc.ABC):
    @abc.abstractmethod
    def extract(self, path, report_date):
        pass

    def __call__(self, path, report_date):
        return self.extract(path, report_date)


class TableExtractionError(Exception):
    pass


def find_table_page(pdf_path) -> Tuple[PageObject, int]:
    """ Return the (1-based) index of the page containing the table table. """
    pdf = PyPDF3.PdfFileReader(str(pdf_path))
    num_pages = pdf.getNumPages()

    for i in range(1, num_pages):  # skip the first page, the table is certainly not there
        page = pdf.getPage(i)
        text = page.extractText().replace('\n', '')
        if TABLE_CAPTION_PATTERN.search(text):
            return page, i + 1  # return a 1-based index
    else:
        raise TableExtractionError('could not find the table in the pdf')


def normalize_table(table: pd.DataFrame) -> pd.DataFrame:
    # Replace '≥90' with ascii equivalent '>=90'
    table.at[9, 'age_group'] = '>=90'
    # Replace 'Età non nota' with english translation
    table.at[10, 'age_group'] = 'unknown'
    return table


def recompute_derived_columns(x: pd.DataFrame) -> pd.DataFrame:
    """ Recompute all derived columns """
    derived_cols = list(cartesian_join(
        COLUMN_PREFIXES, ['cases_percentage', 'deaths_percentage', 'fatality_rate']))
    y = x.drop(columns=derived_cols)  # to avoid SettingWithCopy warning

    total_cases = x['cases'].sum()
    total_deaths = x['deaths'].sum()
    y['cases_percentage'] = x['cases'] / total_cases * 100
    y['deaths_percentage'] = x['deaths'] / total_deaths * 100
    y['fatality_rate'] = x['deaths'] / x['cases'] * 100

    # REMEMBER: male_cases + female_cases != total_cases,
    # because total_cases also includes cases of unknown sex
    for what in ['cases', 'deaths']:
        total = x[f'male_{what}'] + x[f'female_{what}']
        denominator = total.replace(0, 1)  # avoid division by 0
        for sex in ['male', 'female']:
            y[f'{sex}_{what}_percentage'] = x[f'{sex}_{what}'] / denominator * 100

    for sex in ['male', 'female']:
        y[f'{sex}_fatality_rate'] = x[f'{sex}_deaths'] / x[f'{sex}_cases'] * 100

    # sanity check
    for col in derived_cols:
        assert numpy.allclose(y[col], x[col], atol=0.1), \
            '\n' + str(pd.DataFrame({'recomputed': y[col], 'original': x[col]}))

    return y[x.columns]


def sanity_check_with_totals(table: pd.DataFrame, totals):
    columns = cartesian_join(COLUMN_PREFIXES, ['cases', 'deaths'])
    for col in columns:
        actual_sum = table[col].sum()
        if actual_sum != totals[col]:
            raise TableExtractionError(
                f'column "{col}" sum() is inconsistent with the value reported '
                f'in the last row of the table: {actual_sum} != {totals[col]}')


def convert_row(row, converters=CONVERTER_BY_COLUMN):
    return {key: converters[key](value) for key, value in row.items()}
