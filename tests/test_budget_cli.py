"""Integration-style tests for the interactive budget CLI."""

from __future__ import annotations

import budget_cli


def test_menu_can_set_income_run_strategy_and_quit(monkeypatch, capsys) -> None:
    inputs = iter(
        [
            "1",  # set income
            "1000",
            "3",  # run a strategy
            "a",  # 50/30/20
            "6",  # quit
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    budget_cli.menu()

    output = capsys.readouterr().out
    assert "Income is now $1,000.00." in output
    assert "50/30/20 allocation" in output
    assert "Exiting budget allocator." in output


def test_menu_comparison_and_redistribution_flow(monkeypatch, capsys) -> None:
    inputs = iter(
        [
            "1",  # set income
            "1000",
            "3",  # run a strategy
            "a",  # 50/30/20
            "5",  # enter actual spending and view comparison
            "9999",  # Rent (force overage)
            "0",  # Groceries
            "0",  # Insurance
            "0",  # Transportation
            "0",  # Utilities
            "0",  # Dining Out
            "0",  # Entertainment
            "0",  # Shopping
            "0",  # Emergency Fund
            "0",  # Retirement
            "6",  # quit
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    budget_cli.menu()

    output = capsys.readouterr().out
    assert "Total overage:" in output
    assert "Redistribution suggestions" in output
    assert "Rent could absorb" in output
