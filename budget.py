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

def allocate_zero_based(
    income: float,
    categories: dict[str, BudgetCategoryProfile],
    manual_amounts: dict[str, Any] | None = None,
) -> BudgetAllocation:

    if income < 0:
        raise ValueError("Income cannot be negative.")
    categories = deepcopy(categories)
    allocations: dict[str, float] = {}
    warnings: list[str] = []

    source_amounts = manual_amounts if manual_amounts is not None else build_zero_based_suggestion(income, categories)
    if manual_amounts is not None:
        unknown_keys = set(manual_amounts) - set(categories)
        if unknown_keys:
            warnings.append(
                f"Ignored amounts for unknown categories: {', '.join(sorted(unknown_keys))}."
            )
    remaining = round(income, 2)

    for name in categories:
        amount = round(float(source_amounts.get(name, 0.0)), 2)
        if amount < 0:
            raise ValueError("Zero-based budgeting does not allow negative assigned amounts.")
        if amount > remaining:
            raise ValueError(f"{name} would overshoot the remaining budget.")
        allocations[name] = amount
        categories[name]["budgeted_amount"] = amount
        remaining = round(remaining - amount, 2)

    if remaining != 0:
        warnings.append(f"Zero-based plan left {format_money(remaining)} unassigned.")

    return cast(
        BudgetAllocation,
        {
            "strategy": "Zero Based",
            "allocations": allocations,
            "categories": categories,
            "allocated_total": round(sum(allocations.values()), 2),
            "remaining": remaining,
            "warnings": warnings,
        },
    )

def compare_strategies(income: float, categories: dict[str, BudgetCategoryProfile]) -> dict[str, BudgetAllocation]:
    return {
        "50/30/20": allocate_fifty_thirty_twenty(income, categories),
        "Priority Weighted": allocate_priority_weighted(income, categories),
        "Zero Based": allocate_zero_based(income, categories),
    }

def compare_actual_to_budget(
    allocation: BudgetAllocation, actual_spending: dict[str, Any]
) -> BudgetComparisonResult:

    alloc = allocation["allocations"]
    cats = allocation["categories"]
    all_names = sorted(set(alloc) | set(actual_spending.keys()))
    rows: list[BudgetComparisonRow] = []
    total_actual = 0.0
    total_budgeted = 0.0
    overages: set[str] = set()
    under_budget: set[str] = set()

    for name in all_names:
        budgeted_amount = round(float(alloc.get(name, 0.0)), 2)
        actual = round(float(actual_spending.get(name, 0.0)), 2)
        difference = round(actual - budgeted_amount, 2)
        total_actual += actual
        total_budgeted += budgeted_amount

        if budgeted_amount == 0:
            percentage_of_budget: float | None = None
        else:
            percentage_of_budget = (actual / budgeted_amount) * 100

        if actual > budgeted_amount:
            status = "OVER"
            overages.add(name)
        elif actual < budgeted_amount:
            status = "UNDER"
            under_budget.add(name)
        else:
            status = "EVEN"

        profile = cats.get(name)
        tier = profile["tier"] if profile else "Unknown"
        priority = int(profile["priority"]) if profile else 0

        rows.append(
            cast(
                BudgetComparisonRow,
                {
                    "category": name,
                    "budgeted": round(budgeted_amount, 2),
                    "actual": actual,
                    "difference": difference,
                    "percentage_of_budget": percentage_of_budget,
                    "status": status,
                    "tier": tier,
                    "priority": priority,
                },
            )
        )

    rows.sort(key=lambda item: (item["status"] != "OVER", -abs(item["difference"])))
    return cast(
        BudgetComparisonResult,
        {
            "rows": rows,
            "overages": overages,
            "under_budget": under_budget,
            "total_overage": round(sum(max(0.0, row["difference"]) for row in rows), 2),
            "total_surplus": round(sum(max(0.0, -row["difference"]) for row in rows), 2),
            "total_actual": round(total_actual, 2),
            "total_budgeted": round(total_budgeted, 2),
        },
    )

def donor_allowed(overage_row: BudgetComparisonRow, candidate_row: BudgetComparisonRow) -> bool:

    if candidate_row["status"] != "UNDER":
        return False
    if candidate_row["category"] == overage_row["category"]:
        return False
    if candidate_row["tier"] == overage_row["tier"] and candidate_row["priority"] <= overage_row["priority"]:
        return True
    if overage_row["tier"] == "Needs" and candidate_row["tier"] == "Wants":
        return True
    return False

















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
