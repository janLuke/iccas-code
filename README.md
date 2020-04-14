# ICCAS dataset code
This repository contains the code used for generating and updating the 
[ICCAS dataset](https://www.github.com/janLuke/iccas-dataset).

## Brief description of scripts

- `download_reports.py`: function and script for parsing the ISS News page in 
order to retrieve links to all PDF reports and download the ones missing in the
`reports` folder (reports are not included in the git repository because they 
take MBs).

- `make_datasets.py`: function and script for generating a new "single-date" 
dataset for each report in the `reports` folder and updating the "full dataset";
it uses `tabula-py` for extracting data from reports. When run as script, it 
first calls the function `download_missing_reports()` contained in `download_reports.py`.

- `update_dataset.py`: script meant to be run in a cronjob for automatically 
creating and deploying new datasets when a new report is published; it notifies
me (via emails) in case of errors or success. 


## How data extraction works

For each report, the page containing the table is found by extracting the text from 
each page (using [PyPDF3](https://github.com/mstamy2/PyPDF3)) and using a regular 
expression to match the table caption.

Then, the table is extracted from the page using [tabula-py](https://github.com/chezou/tabula-py)* 
with "tabula templates", i.e. JSON files describing where the table is located (page and selection area).
Since the page containing the table is automatically detected, only the "selection area" is actually used.

Templates are stored in the `tabula-templates` folder as `{date of first validity}.tabula-template.json`
and are created using the [Tabula app](https://tabula.technology/) by loading a document 
and manually selecting the area of interest. Fortunately, the table area location has been stable so 
I had to repeat this manual step only two times.

Once data is extracted into a `pandas.DataFrame`, all columns that can be computed from absolute
counts are recomputed (both for having full prevision and for sanity checking). This step may be 
removed in the future.

(*) I quickly tried to extract the table by parsing the text extracted by `PyPDF3` but
the solution required some "hacks", so in the end I preferred using `tabula-py`.