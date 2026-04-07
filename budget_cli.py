from __future__ import annotations

from typing import cast

import budget
from schemas import BudgetAllocation, BudgetCategoryProfile, BudgetComparisonResult
from storage import format_money

def print_allocation_table(allocation: BudgetAllocation) -> None:
    print(f"{allocation['strategy']} allocation")
    print(f"{'Category':<18}{'Tier':<10}{'Weight':>8}{'Budgeted':>16}")
    print("-" * 52)
    for name, info in allocation["categories"].items():
        amount = format_money(allocation["allocations"].get(name, 0.0))
        print(f"{name:<18}{info['tier']:<10}{info['weight']:>8}{amount:>16}")
    print("-" * 52)
    print(f"Allocated total: {format_money(allocation['allocated_total'])}")
    print(f"Remaining: {format_money(allocation['remaining'])}")
    for warning in allocation["warnings"]:
        print(f"Warning: {warning}")

def print_strategy_comparison_table(results: dict[str, BudgetAllocation]) -> None:
    if not results:
        print("No strategies to compare.")
        return
    categories = list(next(iter(results.values()))["categories"])
    header = f"{'Category':<18}"
    for strategy_name in results:
        header += f"{strategy_name[:16]:>18}"
    print(header)
    print("-" * len(header))
    for category in categories:
        line = f"{category:<18}"
        for _strategy_name, result in results.items():
            line += f"{format_money(result['allocations'].get(category, 0.0)):>18}"
        print(line)

def print_comparison_report(comparison: BudgetComparisonResult, income: float) -> None:
    print(f"{'Category':<18}{'Budgeted':>14}{'Actual':>14}{'Difference':>14}{'Status':>10}")
    print("-" * 70)
    for row in comparison["rows"]:
        marker = "**" if row["status"] == "OVER" else ""
        pct = row["percentage_of_budget"]
        detail = f"{pct:.0f}%" if pct is not None else "n/a"
        print(
            f"{row['category']:<18}"
            f"{format_money(row['budgeted']):>14}"
            f"{format_money(row['actual']):>14}"
            f"{format_money(row['difference']):>14}"
            f"{(marker + row['status'] + ' ' + detail):>10}"
        )

    print("-" * 70)
    print(f"Total income: {format_money(income)}")
    print(f"Total budgeted: {format_money(comparison['total_budgeted'])}")
    print(f"Total spent: {format_money(comparison['total_actual'])}")
    print(f"Total overage: {format_money(comparison['total_overage'])}")
    print(f"Total surplus: {format_money(comparison['total_surplus'])}")

    suggestions = budget.build_redistribution_suggestions(comparison)
    if suggestions:
        print()
        print("Redistribution suggestions")
        for suggestion in suggestions:
            donor_text = ", ".join(f"{item['from']} {format_money(item['amount'])}" for item in suggestion["donors"])
            print(f"{suggestion['category']} could absorb {format_money(suggestion['needed'])} from {donor_text}")

def prompt_float(prompt: str, allow_zero: bool = True) -> float | None:
    entered = input(prompt).strip()
    try:
        value = float(entered)
    except ValueError:
        print("Please enter a numeric value.")
        return None
    if value < 0:
        print("Negative values are not allowed here.")
        return None
    if value == 0 and not allow_zero:
        print("Zero is not allowed for this field.")
        return None
    return value

def add_category(categories: dict[str, BudgetCategoryProfile]) -> None:
    existing: set[str] = set(categories)
    name = input("Category name: ").strip()
    tier = input("Tier (Needs/Wants/Savings): ").strip().title()
    weight = input("Weight: ").strip()
    priority = input("Priority 1-10: ").strip()
    try:
        info = {"tier": tier, "weight": float(weight), "priority": int(priority), "actual_spend": 0.0, "budgeted_amount": 0.0}
    except ValueError:
        print("Weight and priority have to be numeric.")
        return
    errors = budget.validate_category(name, info, existing)
    if errors:
        for error in errors:
            print(error)
        return
    categories[name] = cast(BudgetCategoryProfile, info)
    print(f"Added {name}.")
# 
def edit_category(categories: dict[str, BudgetCategoryProfile]) -> None:
    name = input("Category to edit: ").strip()
    if name not in categories:
        print("That category was not found.")
        return
    info = categories[name]
    new_tier = input(f"Tier [{info['tier']}]: ").strip().title() or info["tier"]
    new_weight_text = input(f"Weight [{info['weight']}]: ").strip()
    new_priority_text = input(f"Priority [{info['priority']}]: ").strip()
    try:
        updated = {
            "tier": new_tier,
            "weight": float(new_weight_text) if new_weight_text else float(info["weight"]),
            "priority": int(new_priority_text) if new_priority_text else int(info["priority"]),
            "actual_spend": float(info["actual_spend"]),
            "budgeted_amount": float(info["budgeted_amount"]),
        }
    except ValueError:
        print("Weight and priority have to stay numeric.")
        return
    errors = budget.validate_category(name, updated, set(categories) - {name})
    if errors:
        for error in errors:
            print(error)
        return
    categories[name] = cast(BudgetCategoryProfile, updated)
    print(f"Updated {name}.")

def remove_category(categories: dict[str, BudgetCategoryProfile]) -> None:
    name = input("Category to remove: ").strip()
    if name in categories:
        categories.pop(name)
        print(f"Removed {name}.")
    else:
        print("That category was not found.")

def enter_actual_spending(categories: dict[str, BudgetCategoryProfile]) -> dict[str, float]:
    actuals: dict[str, float] = {}
    for name in categories:
        entered = input(f"Actual spending for {name} [0]: ").strip()
        if not entered:
            actuals[name] = 0.0
            continue
        try:
            amount = float(entered)
            if amount < 0:
                print("Negative actual spending is not allowed, so I used 0 instead.")
                amount = 0.0
            actuals[name] = amount
        except ValueError:
            print("That number was invalid, so I used 0 instead.")
            actuals[name] = 0.0
    return actuals

def menu() -> None:
    income = 0.0
    categories = budget.starter_categories()
    actual_spending: dict[str, float] = {}
    last_allocation: BudgetAllocation | None = None
    valid_choices = {"1", "2", "3", "4", "5", "6"}

    while True:
        print()
        print("LedgerLogic: Priority-Based Budget Distributor")
        print("1. Set income")
        print("2. Manage categories")
        print("3. Run a strategy")
        print("4. Run all strategies and compare")
        print("5. Enter actual spending / view comparison")
        print("6. Quit")
        choice = input("Choose an option: ").strip()
        if choice not in valid_choices:
            print("Please choose a valid menu number.")
            continue

        if choice == "1":
            new_income = prompt_float("Monthly income: ", allow_zero=True)
            if new_income is not None:
                income = new_income
                print(f"Income is now {format_money(income)}.")

        elif choice == "2":
            print("a. Add category")
            print("b. Edit category")
            print("c. Remove category")
            print("d. View categories")
            sub = input("Choice: ").strip().lower()
            if sub == "a":
                add_category(categories)
            elif sub == "b":
                edit_category(categories)
            elif sub == "c":
                remove_category(categories)
            elif sub == "d":
                for name, info in categories.items():
                    print(f"{name:<18}{info['tier']:<10}{info['weight']:>6}{info['priority']:>6}")
            else:
                print("That category option was not recognized.")

        elif choice == "3":
            if not categories:
                print("Please add at least one category first.")
                continue
            if income == 0:
                print("Income is zero, so the plan will be all zeros unless you change it.")
            print("a. 50/30/20")
            print("b. Priority weighted")
            print("c. Zero based")
            sub = input("Strategy: ").strip().lower()
            try:
                if sub == "a":
                    last_allocation = budget.allocate_fifty_thirty_twenty(income, categories)
                elif sub == "b":
                    last_allocation = budget.allocate_priority_weighted(income, categories)
                elif sub == "c":
                    last_allocation = budget.allocate_zero_based(income, categories)
                else:
                    print("That strategy key was not recognized.")
                    continue
                print_allocation_table(last_allocation)
            except ValueError as error:
                print(f"Could not run strategy: {error}")

        elif choice == "4":
            if not categories:
                print("Please add categories first.")
                continue
            try:
                results = budget.compare_strategies(income, categories)
                print_strategy_comparison_table(results)
            except ValueError as error:
                print(f"Could not compare strategies: {error}")

        elif choice == "5":
            if last_allocation is None:
                print("Run a strategy first so there is a budget to compare against.")
                continue
            actual_spending = enter_actual_spending(categories)
            comparison = budget.compare_actual_to_budget(last_allocation, actual_spending)
            print_comparison_report(comparison, income)

        elif choice == "6":
            print("Exiting budget allocator.")
            break