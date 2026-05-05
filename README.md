# Budgeting Dashboard
**Version 0.1** | By Matthew Ian Connor

An interactive personal finance dashboard built with Plotly Dash. Load your transaction data as a CSV and explore your spending and income through charts, statistics, and a budget planner — all in your browser.

## Features

- **Spending by Proportion** — Pie chart of spending by category, with drilldown into sub-categories. Filter by month or view all time. Toggle between spending and income.
- **Month over Month** — Bar chart comparing spending trends across months, with category filtering and drilldown.
- **Descriptive Statistics** — Table of summary stats (avg, min, max, etc.) by category and sub-category. Filter by month or view all time.
- **Over Time** — Line chart of spending and income trends over time.
- **Budget Planner** — Set monthly budget targets for each expense and income sub-category. See average, min, and max actuals alongside your budget, with over/under indicators. Includes a budget review summary with net income vs. expenses.

## Requirements

- Python 3.8+
- The following Python packages:
  - `dash`
  - `dash-bootstrap-components`
  - `pandas`
  - `plotly`

Install them with:

```bash
pip install dash dash-bootstrap-components pandas plotly
```

## Usage

1. Clone or download this repository.
2. Place your transaction CSV file in the same folder as `budgeting_dashboard.py` and name it `budgeting_data.csv`.
3. Run the script:

```bash
python budgeting_dashboard.py
```

4. Your browser will open automatically to `http://127.0.0.1:8050`. Click **Exit** in the dashboard to shut it down.

## CSV Format

Your `budgeting_data.csv` must contain the following columns:

| Column | Description |
|---|---|
| `Transaction Date` | Date of the transaction (any standard date format) |
| `Amount` | Transaction amount. Income should be positive, spending negative. |
| `Category name` | Top-level category (e.g. `Food`, `Housing`, `Income`) |
| `Sub-category name` | Sub-category (e.g. `Groceries`, `Rent`, `Paycheck`) |
| `Transaction Type` | Included in the file but not used by the dashboard |

Transactions with `Category name` equal to `Income` are treated as income; all others are treated as spending.
