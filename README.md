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
When run as script, it first calls the function `download_missing_reports()` 
contained in `download_reports.py`.

- `update_dataset.py`: script meant to be run in a cronjob for automatically 
creating and deploying new datasets when a new report is published; it notifies
me (via emails) in case of errors or success. 
