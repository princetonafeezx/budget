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

def aggregate_actual_spending(records: list[CategorizedRecord]) -> dict[str, float]:
    
    totals: dict[str, float] = {}
    for record in records:
        raw = str(record.get("subcategory") or record.get("category") or "Unknown")
        category_name = normalize_actual_spending_category(raw)
        if category_name not in totals:
            totals[category_name] = 0.0
        totals[category_name] += float(record.get("amount", 0.0))
    return {key: round(value, 2) for key, value in totals.items()}

def validate_category(name: str, info: dict[str, Any], existing_names: set[str]) -> list[str]:
    
    errors = []
    if not name:
        errors.append("Category name cannot be blank.")
    if info.get("tier") not in VALID_TIERS:
        errors.append("Tier must be Needs, Wants, or Savings.")
    try:
        if float(info.get("weight", 0)) < 0:
            errors.append("Weight cannot be negative.")
    except (TypeError, ValueError):
        errors.append("Weight has to be numeric.")
    try:
        priority = int(info.get("priority", 0))
        if priority < 1 or priority > 10:
            errors.append("Priority should be from 1 to 10.")
    except (TypeError, ValueError):
        errors.append("Priority has to be a whole number.")
    if name in existing_names:
        errors.append("Duplicate category names are not allowed.")
    return errors






















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
