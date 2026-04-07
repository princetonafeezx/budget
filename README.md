App: Priority-Based Budget Distributor

What it does: Given a monthly income and a list of expense categories with priority levels (needs vs. wants vs. savings), it distributes the budget using multiple strategies: 50/30/20 rule, priority-weighted allocation, and zero-based budgeting. Compares actual spending (from Day 8) against the budget and highlights overages.

Why it matters: Multiple sorting algorithms, priority queues, and comparison logic. The budget-vs-actual comparison is a set operation (finding differences between two data structures). Key skills: Sorting with custom comparators, priority-based allocation algorithms, set operations (budget categories vs. actual categories), percentage calculations, and variance analysis.

Standalone value: Create and evaluate a budget against real spending.

Mega-app role: ledgerlogic/budget.py —the planning and comparison engine.

Include all these features:

Budget Distribution Strategies
•	50/30/20 rule: auto-splits income into 50% Needs, 30% Wants, 20% Savings, then distributes within each tier proportionally by category weight
•	Priority-weighted allocation: user assigns a priority score (1–10) to each category, budget distributed proportionally by score across all categories
•	Zero-based budgeting: every dollar assigned manually until remaining balance hits zero, enforces no overshoot
•	Side-by-side comparison table showing how each strategy allocates differently
Category & Priority System
•	Predefined starter categories (Rent, Groceries, Insurance, Dining Out, Entertainment, Emergency Fund, etc.) that the user can accept or customize
•	Three priority tiers: Needs, Wants, Savings — each category assigned to one tier
•	Optional weight/importance value within a tier (e.g., Rent is more important than Utilities, both are Needs)
•	Dictionary-based category storage: name → {tier, weight, actual_spend, budgeted_amount}
Actual vs Budget Comparison
•	Input actual spending per category after budget is generated
•	Overage detection: flags any category where actual exceeds budget with the dollar amount over
•	Under-budget detection: shows categories with money left over
•	Percentage-based comparison (e.g., "Dining Out: 142% of budget — $63 over")
•	Total overage and total surplus summary line
Redistribution Suggestions
•	When overages exist, suggests which under-budget categories could absorb the excess
•	Only pulls from same-tier or lower-priority categories (won't raid Savings to cover Wants)
•	Shows a proposed rebalanced budget using leftover amounts
Dictionary, Set & Control Flow Showcase
•	Nested dictionary for full category profiles (tier, weight, amounts)
•	Dictionary mapping strategy names to their distribution functions for clean dispatch
•	Set of valid tier names for input validation
•	Set operations to find categories with overages vs under-budget (set intersection/difference patterns)
•	Sets tracking which categories have been assigned in zero-based mode to prevent double-allocation
•	Complex control flow: nested loops for distributing within tiers, if/elif chains for strategy branching, while loops for zero-based until balance is zero
Formatted Output
•	Aligned table output for each strategy with columns: Category, Tier, Weight, Budgeted Amount
•	Comparison table with columns: Category, Budgeted, Actual, Difference, Status (✓ or OVER)
•	Summary section: total income, total allocated, total spent, net difference
•	Color-coded status using simple terminal markers (** for overages, nothing for okay)
CLI Interface
•	Menu-driven loop: set income, manage categories, run a strategy, run all strategies and compare, enter actual spending, view comparison report, quit
•	Add/edit/remove categories at any time with validation against duplicate names
•	Strategy selection submenu to pick one or compare all three
•	Ability to re-run with a different income without re-entering categories
•	Input validation on all numeric fields and tier assignments
Edge Case Handling
•	Zero income: handled gracefully with a message, no division by zero
•	No categories defined: prompts user to add at least one before running
•	All categories in one tier (e.g., everything is "Needs"): 50/30/20 still works, assigns full 50% pool, warns the other tiers are empty
•	Weights that sum to zero within a tier: caught and reported
•	Actual spending entered as zero: treated as valid, shows fully under-budget
•	Negative input: rejected everywhere with clear messages
Code Quality (6-month student level)
•	Single file, function-based, no classes or imports beyond built-in modules
•	Docstrings with a student's voice ("This function loops through each category and figures out how much money it should get based on its weight")
•	Some copy-paste patterns between the three strategy functions — a student who sees the repetition but hasn't refactored into a generic engine yet
•	A few too-long functions (the comparison report builder) that a more experienced dev would split
•	Inconsistent formatting in places: some f-strings, some .format(), one or two string concatenations — realistic for a learner still finding their style
•	Comments heavy in the tricky sections (zero-based loop), sparse in the straightforward ones

