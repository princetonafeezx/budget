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