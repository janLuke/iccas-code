import re

import pandas as pd

from table_extraction.common import (
    TableExtractor,
    find_table_page,
    COLUMNS,
    COLUMN_CONVERTERS,
    normalize_table
)


class PyPDFTableExtractor(TableExtractor):
    unknown_age_matcher = re.compile('(età non nota|non not[ao])', flags=re.IGNORECASE)

    def extract(self, path, report_date: str) -> pd.DataFrame:
        page, _ = find_table_page(path)
        # For some reason, the extracted text contains a lot of superfluous newlines
        text = page.extractText().replace('\n', '')
        text = self.unknown_age_matcher.sub('unknown', text)
        start = text.find('0-9')
        text = text[start:]
        text = text.replace(', ', ',')   # from 28/09, they write "1,5" as "1, 5"
        tokens = text.split(' ')
        num_rows = 11
        num_columns = len(COLUMNS)
        rows = []
        for i in range(num_rows):
            start = i * num_columns
            end = start + num_columns
            row = tokens[start:end]
            for j in range(num_columns):
                row[j] = COLUMN_CONVERTERS[j](row[j])
            rows.append(row)
        df = pd.DataFrame(rows, columns=COLUMNS)

        return normalize_table(df)
