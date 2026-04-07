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
