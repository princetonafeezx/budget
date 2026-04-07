# ll_budget

`Ledger Logic Budget` is a terminal-first budgeting app that helps plan monthly spending,
compare budget vs actuals, and suggest simple redistribution when categories go
over budget.

## Features

- Three allocation strategies:
  - `50/30/20` split by tier with weight-based distribution in each tier
  - `Priority Weighted` allocation across all categories using priority scores
  - `Zero Based` allocation with overshoot protection
- Budget vs actual comparison with:
  - per-category over/under/even status
  - percentage-of-budget calculation
  - total overage and total surplus summaries
- Redistribution suggestions with conservative donor rules
- Starter categories and interactive category management
- Shared parsing/storage helpers and typed data contracts

## Project structure

- `budget.py`: core budget domain logic (allocation, comparison, suggestions)
- `budget_cli.py`: CLI menu, prompts, and terminal output rendering
- `parsing.py`: shared date and amount parsing helpers
- `storage.py`: CSV/JSON/text persistence with atomic writes
- `schemas.py`: `TypedDict` contracts used across modules
- `tests/`: unit and integration-style tests

## Run locally

```bash
python budget.py
```

## Run tests

```bash
pytest -q
```

## Quick example session

```text
$ python budget.py
LedgerLogic: Priority-Based Budget Distributor
1. Set income
2. Manage categories
3. Run a strategy
4. Run all strategies and compare
5. Enter actual spending / view comparison
6. Quit

Choose an option: 1
Monthly income: 5000
Income is now $5,000.00.

Choose an option: 3
Strategy: a
50/30/20 allocation
...

Choose an option: 5
Actual spending for Rent [0]: 2600
...
Total overage: $...
Redistribution suggestions
...
```

## Notes

- The CLI is intentionally simple and menu-driven.
- The codebase now separates domain logic from CLI concerns to improve
  maintainability and testability.
