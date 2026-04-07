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

def apply_actual_spending(
    categories: dict[str, BudgetCategoryProfile], actual_spending: dict[str, Any] | None
) -> dict[str, BudgetCategoryProfile]:
    
    categories = deepcopy(categories)
    actual_spending = actual_spending or {}
    for name, info in categories.items():
        info["actual_spend"] = round(float(actual_spending.get(name, 0.0)), 2)
    return categories

def distribute_pool_by_weight(
    category_names: list[str], categories: dict[str, BudgetCategoryProfile], pool_amount: float
) -> tuple[dict[str, float], list[str]]:
    warnings = []
    allocations: dict[str, float] = {}
    total_weight = 0.0
    for name in category_names:
        total_weight += float(categories[name]["weight"])

    if total_weight == 0:
        warnings.append("Weights summed to zero for one allocation pool, so nothing was assigned there.")
        for name in category_names:
            allocations[name] = 0.0
        return allocations, warnings

    running_total = 0.0
    for index, name in enumerate(category_names, start=1):
        if index == len(category_names):
            amount = round(pool_amount - running_total, 2)
        else:
            share = float(categories[name]["weight"]) / total_weight
            amount = round(pool_amount * share, 2)
            running_total += amount
        allocations[name] = max(0.0, amount)
    return allocations, warnings

def allocate_fifty_thirty_twenty(income: float, categories: dict[str, BudgetCategoryProfile]) -> BudgetAllocation:

    if income < 0:
        raise ValueError("Income cannot be negative.")
    categories = deepcopy(categories)
    tier_pools = {"Needs": income * 0.50, "Wants": income * 0.30, "Savings": income * 0.20}
    warnings = []
    allocations: dict[str, float] = {}

    for tier_name, pool in tier_pools.items():
        tier_names = [name for name, info in categories.items() if info["tier"] == tier_name]
        if not tier_names:
            warnings.append(f"The {tier_name} tier had no categories, so its pool stayed unassigned.")
            continue
        tier_allocations, pool_warnings = distribute_pool_by_weight(tier_names, categories, round(pool, 2))
        warnings.extend(pool_warnings)
        allocations.update(tier_allocations)

    allocated_total = sum(allocations.values())
    for name, amount in allocations.items():
        categories[name]["budgeted_amount"] = amount

    return cast(
        BudgetAllocation,
        {
            "strategy": "50/30/20",
            "allocations": allocations,
            "categories": categories,
            "allocated_total": round(allocated_total, 2),
            "remaining": round(income - allocated_total, 2),
            "warnings": warnings,
        },
    )

def allocate_priority_weighted(income: float, categories: dict[str, BudgetCategoryProfile]) -> BudgetAllocation:

    if income < 0:
        raise ValueError("Income cannot be negative.")
    categories = deepcopy(categories)
    allocations: dict[str, float] = {}
    total_priority = 0
    for info in categories.values():
        total_priority += int(info["priority"])

    if total_priority == 0:
        raise ValueError("Priority scores cannot sum to zero.")

    running_total = 0.0
    names = list(categories)
    for index, name in enumerate(names, start=1):
        if index == len(names):
            amount = round(income - running_total, 2)
        else:
            share = int(categories[name]["priority"]) / total_priority
            amount = round(income * share, 2)
            running_total += amount
        allocations[name] = max(0.0, amount)
        categories[name]["budgeted_amount"] = allocations[name]

    return cast(
        BudgetAllocation,
        {
            "strategy": "Priority Weighted",
            "allocations": allocations,
            "categories": categories,
            "allocated_total": round(sum(allocations.values()), 2),
            "remaining": round(income - sum(allocations.values()), 2),
            "warnings": [],
        },
    )

def build_zero_based_suggestion(income: float, categories: dict[str, BudgetCategoryProfile]) -> dict[str, float]:

    ordered_names = sorted(
        categories,
        key=lambda name: (
            TIER_RANK.get(str(categories[name]["tier"]), 99),
            -int(categories[name]["priority"]),
            -float(categories[name]["weight"]),
        ),
    )
    remaining = round(income, 2)
    allocations: dict[str, float] = {}
    assigned: set[str] = set()

    total_priority = sum(int(info["priority"]) for info in categories.values()) or 1
    for index, name in enumerate(ordered_names, start=1):
        if name in assigned:
            continue
        if index == len(ordered_names):
            amount = remaining
        else:
            share = int(categories[name]["priority"]) / total_priority
            amount = round(income * share, 2)
            if amount > remaining:
                amount = remaining
        allocations[name] = max(0.0, amount)
        remaining = round(remaining - allocations[name], 2)
        assigned.add(name)

    return allocations





















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
