"""Priority-based budget distributor."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

from schemas import (
    BudgetAllocation,
    BudgetCategoryProfile,
    BudgetComparisonResult,
    BudgetComparisonRow,
    CategorizedRecord,
    )
from storage import format_money

VALID_TIERS = {"Needs", "Wants", "Savings"}
TIER_RANK = {"Needs": 0, "Wants": 1, "Savings": 2}

ACTUAL_SPEND_CATEGORY_ALIASES: dict[str, str] = {"Health": "Insurance"}

def normalize_actual_spending_category(raw_name: str) -> str:
    return ACTUAL_SPEND_CATEGORY_ALIASES.get(raw_name, raw_name)

def starter_categories() -> dict[str, BudgetCategoryProfile]:
    
    return cast(
        dict[str, BudgetCategoryProfile],
        {
            "Rent": {"tier": "Needs", "weight": 5, "priority": 10, "actual_spend": 0.0, "budgeted_amount": 0.0},
            "Groceries": {"tier": "Needs", "weight": 4, "priority": 9, "actual_spend": 0.0, "budgeted_amount": 0.0},
            "Insurance": {"tier": "Needs", "weight": 3, "priority": 8, "actual_spend": 0.0, "budgeted_amount": 0.0},
            "Transportation": {"tier": "Needs", "weight": 3, "priority": 7, "actual_spend": 0.0, "budgeted_amount": 0.0},
            "Utilities": {"tier": "Needs", "weight": 3, "priority": 7, "actual_spend": 0.0, "budgeted_amount": 0.0},
            "Dining Out": {"tier": "Wants", "weight": 2, "priority": 4, "actual_spend": 0.0, "budgeted_amount": 0.0},
            "Entertainment": {"tier": "Wants", "weight": 2, "priority": 4, "actual_spend": 0.0, "budgeted_amount": 0.0},
            "Shopping": {"tier": "Wants", "weight": 2, "priority": 3, "actual_spend": 0.0, "budgeted_amount": 0.0},
            "Emergency Fund": {"tier": "Savings", "weight": 3, "priority": 9, "actual_spend": 0.0, "budgeted_amount": 0.0},
            "Retirement": {"tier": "Savings", "weight": 4, "priority": 10, "actual_spend": 0.0, "budgeted_amount": 0.0},
        },
    )
























def menu() -> None:
    try:
        from .budget_cli import menu as cli_menu
    except ImportError:
        from budget_cli import menu as cli_menu
    cli_menu()


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
