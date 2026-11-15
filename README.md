# Manchester Housing Data Analysis

Exploratory data analysis of the Manchester housing dataset (19,999 sales)
for the Arden University module *Programming for Data Analytics*. The project
answers three questions:

1. How do waterfront properties differ from the rest of the market?
2. How is floor space related to price?
3. Is the year a property was built (`built`) correlated with price?

## Project structure

```
Manchester_housing_Data_Analysis/
├── data/raw/                      raw dataset (Manchester_house_Dataset[3678].csv)
├── src/
│   ├── config.py                  paths, file names and analysis settings
│   ├── logger.py                  one log file per run in logs/
│   ├── exception.py               CustomException with file and line number
│   ├── utils.py                   shared helpers (summary table, IQR outliers)
│   ├── components/
│   │   ├── data_ingestion.py      find and load the raw CSV
│   │   ├── data_preprocessing.py  type correction, audit, cleaning
│   │   ├── eda_analysis.py        statistics for the three questions
│   │   └── visualisation.py       Figures 1-6
│   └── pipeline/
│       └── run_pipeline.py        runs everything in order
├── tests/                         unit tests (pytest)
├── artifacts/                     outputs: clean data, tables, figures
├── logs/                          run logs
├── requirements.txt
└── setup.py
```

## Set-up (once)

```bash
cd "/Volumes/E Drive/Learning Curve/Arden Univeristy /1st Semester/Manchester_housing_Data_Analysis"
conda activate ./venv
pip install -r requirements.txt
```

## Run

```bash
python -m src.pipeline.run_pipeline   # full analysis -> artifacts/
python -m pytest                      # unit tests
```

Always start commands from the project folder and use `python -m ...`, so
that Python can find the `src` package.

## Outputs

| Path | Content |
| --- | --- |
| `artifacts/manchester_housing_clean.csv` | cleaned dataset (19,997 rows) |
| `artifacts/tables/01-11_*.csv` | statistics, audit, test and regression results |
| `artifacts/figures/fig1-6_*.png` | charts used in the report |
| `logs/<date_time>.log` | step-by-step log of the run |

## Coding standards

PEP 8 (checked with `flake8`), docstrings for every module, class and
function, constants in `src/config.py`, no hard-coded paths elsewhere, and a
fixed random seed (`RANDOM_STATE = 42`) for reproducible results.
