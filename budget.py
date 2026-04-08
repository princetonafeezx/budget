from __future__ import annotations # Enable postponed evaluation of type annotations for forward compatibility

from copy import deepcopy # Import deepcopy to create independent copies of nested dictionary structures
from typing import Any, cast # Import Any for flexible typing and cast to help the type checker with specific returns


from schemas import ( # Import schemas from the current working directory
    BudgetAllocation,
    BudgetCategoryProfile,
    BudgetComparisonResult,
    BudgetComparisonRow,
    CategorizedRecord,
)
from storage import format_money # Import formatting utility from the current working directory

VALID_TIERS = {"Needs", "Wants", "Savings"} # Define the set of allowed financial priority tiers
TIER_RANK = {"Needs": 0, "Wants": 1, "Savings": 2} # Map tiers to numeric ranks for sorting logic

ACTUAL_SPEND_CATEGORY_ALIASES: dict[str, str] = {"Health": "Insurance"} # Map specific merchant labels to budget category names


def normalize_actual_spending_category(raw_name: str) -> str: # Define a function to fix naming mismatches in spending data
    """Map transaction labels onto :func:`starter_categories` keys.""" # Docstring explaining the category mapping
    return ACTUAL_SPEND_CATEGORY_ALIASES.get(raw_name, raw_name) # Return the alias if it exists, otherwise return the original name


def starter_categories() -> dict[str, BudgetCategoryProfile]: # Define a function to provide a default set of budget categories
    """Return a starter category set that the user can customize.""" # Docstring for the category generator
    return cast( # Tell the type checker that this specific dictionary matches the BudgetCategoryProfile format
        dict[str, BudgetCategoryProfile], # The expected dictionary type
        { # Start of the default category dictionary
            "Rent": {"tier": "Needs", "weight": 5, "priority": 10, "actual_spend": 0.0, "budgeted_amount": 0.0}, # High priority housing
            "Groceries": {"tier": "Needs", "weight": 4, "priority": 9, "actual_spend": 0.0, "budgeted_amount": 0.0}, # Essential food
            "Insurance": {"tier": "Needs", "weight": 3, "priority": 8, "actual_spend": 0.0, "budgeted_amount": 0.0}, # Protection
            "Transportation": {"tier": "Needs", "weight": 3, "priority": 7, "actual_spend": 0.0, "budgeted_amount": 0.0}, # Commuting
            "Utilities": {"tier": "Needs", "weight": 3, "priority": 7, "actual_spend": 0.0, "budgeted_amount": 0.0}, # Electricity and water
            "Dining Out": {"tier": "Wants", "weight": 2, "priority": 4, "actual_spend": 0.0, "budgeted_amount": 0.0}, # Leisure eating
            "Entertainment": {"tier": "Wants", "weight": 2, "priority": 4, "actual_spend": 0.0, "budgeted_amount": 0.0}, # Fun and media
            "Shopping": {"tier": "Wants", "weight": 2, "priority": 3, "actual_spend": 0.0, "budgeted_amount": 0.0}, # Non-essential items
            "Emergency Fund": {"tier": "Savings", "weight": 3, "priority": 9, "actual_spend": 0.0, "budgeted_amount": 0.0}, # Safety net
            "Retirement": {"tier": "Savings", "weight": 4, "priority": 10, "actual_spend": 0.0, "budgeted_amount": 0.0}, # Long term future
        }, # End of default categories
    ) # End of cast


def aggregate_actual_spending(records: list[CategorizedRecord]) -> dict[str, float]: # Define a function to sum transactions by category
    """Roll transaction rows into budget category keys (aliases applied).""" # Docstring for transaction aggregation
    totals: dict[str, float] = {} # Initialize an empty dictionary for the category sums
    for record in records: # Iterate through every individual transaction record
        raw = str(record.get("subcategory") or record.get("category") or "Unknown") # Get a category label, preferring specific subcategories
        category_name = normalize_actual_spending_category(raw) # Align the label with the budget's naming convention
        if category_name not in totals: # If this is the first time seeing this category
            totals[category_name] = 0.0 # Set the starting sum to zero
        totals[category_name] += float(record.get("amount", 0.0)) # Add the transaction amount to the category total
    return {key: round(value, 2) for key, value in totals.items()} # Return the totals rounded to two decimal places


def validate_category(name: str, info: dict[str, Any], existing_names: set[str]) -> list[str]: # Define a function to check category data integrity
    """Validate one category profile.""" # Docstring for the validation logic
    errors = [] # Initialize a list to hold error messages
    if not name: # Check if the category name is missing
        errors.append("Category name cannot be blank.") # Add an error for empty names
    if info.get("tier") not in VALID_TIERS: # Check if the assigned tier is one of the allowed three
        errors.append("Tier must be Needs, Wants, or Savings.") # Add an error for invalid tiers
    try: # Attempt to process the weight value
        if float(info.get("weight", 0)) < 0: # Check if weight is negative
            errors.append("Weight cannot be negative.") # Add an error for negative weights
    except (TypeError, ValueError): # Catch cases where weight is not a number
        errors.append("Weight has to be numeric.") # Add an error for non-numeric weights
    try: # Attempt to process the priority value
        priority = int(info.get("priority", 0)) # Convert priority to an integer
        if priority < 1 or priority > 10: # Check if priority is outside the 1-10 range
            errors.append("Priority should be from 1 to 10.") # Add an error for out-of-range priority
    except (TypeError, ValueError): # Catch cases where priority is not an integer
        errors.append("Priority has to be a whole number.") # Add an error for non-integer priority
    if name in existing_names: # Check if the name is already taken by another category
        errors.append("Duplicate category names are not allowed.") # Add an error for duplicates
    return errors # Return the full list of found issues


def apply_actual_spending( # Define a function to inject real spending data into budget profiles
    categories: dict[str, BudgetCategoryProfile], actual_spending: dict[str, Any] | None # Accept current categories and spend data
) -> dict[str, BudgetCategoryProfile]: # Indicate that a modified category dictionary is returned
    """Copy actual spend values into the category profiles.""" # Docstring for the spending update
    categories = deepcopy(categories) # Create a fresh copy to avoid modifying the original data
    actual_spending = actual_spending or {} # Ensure spending data is a dictionary even if None was passed
    for name, info in categories.items(): # Iterate through each category profile
        info["actual_spend"] = round(float(actual_spending.get(name, 0.0)), 2) # Update the profile with rounded actual spend
    return categories # Return the updated categories


def distribute_pool_by_weight( # Define a helper for splitting a specific sum of money based on weight ratios
    category_names: list[str], categories: dict[str, BudgetCategoryProfile], pool_amount: float # Accept categories and target amount
) -> tuple[dict[str, float], list[str]]: # Return the specific allocations and any warnings generated
    """Split one pool across a tier based on weight.""" # Docstring for weighted distribution
    warnings = [] # Initialize a list for warnings
    allocations: dict[str, float] = {} # Initialize a dictionary for the results
    total_weight = 0.0 # Initialize a counter for the denominator
    for name in category_names: # Iterate through the names in this specific pool
        total_weight += float(categories[name]["weight"]) # Sum up the weights to establish ratios

    if total_weight == 0: # Check if no weights were assigned to this group
        warnings.append("Weights summed to zero for one allocation pool, so nothing was assigned there.") # Log the zero-weight issue
        for name in category_names: # For every name in this group
            allocations[name] = 0.0 # Assign zero dollars
        return allocations, warnings # Return early with the empty allocations

    running_total = 0.0 # Track how much has been assigned to prevent rounding errors
    for index, name in enumerate(category_names, start=1): # Iterate through names with an index counter
        if index == len(category_names): # Check if we are on the very last category in the list
            amount = round(pool_amount - running_total, 2) # Assign the entire remainder to ensure exactly zero dollars left
        else: # For all other categories
            share = float(categories[name]["weight"]) / total_weight # Calculate this category's percentage of the total weight
            amount = round(pool_amount * share, 2) # Calculate the dollar amount and round to cents
            running_total += amount # Add this amount to the running total
        allocations[name] = max(0.0, amount) # Ensure no negative amounts and store the result
    return allocations, warnings # Return the completed distribution


def allocate_fifty_thirty_twenty(income: float, categories: dict[str, BudgetCategoryProfile]) -> BudgetAllocation: # Strategy: 50/30/20
    """Apply the 50/30/20 rule and distribute within tiers.""" # Docstring for the standard ratio strategy
    if income < 0: # Check for invalid income input
        raise ValueError("Income cannot be negative.") # Stop execution if income is negative
    categories = deepcopy(categories) # Work on a copy of the categories
    tier_pools = {"Needs": income * 0.50, "Wants": income * 0.30, "Savings": income * 0.20} # Calculate the three main dollar pools
    warnings = [] # Initialize a list for logic warnings
    allocations: dict[str, float] = {} # Initialize a dictionary for specific category amounts

    for tier_name, pool in tier_pools.items(): # Process each of the three tiers one by one
        tier_names = [name for name, info in categories.items() if info["tier"] == tier_name] # Find categories belonging to this tier
        if not tier_names: # Check if a tier has no assigned categories
            warnings.append(f"The {tier_name} tier had no categories, so its pool stayed unassigned.") # Log the unassigned money
            continue # Move to the next tier
        tier_allocations, pool_warnings = distribute_pool_by_weight(tier_names, categories, round(pool, 2)) # Split the tier's money
        warnings.extend(pool_warnings) # Collect any warnings from the distribution logic
        allocations.update(tier_allocations) # Add these results to the main allocation list

    allocated_total = sum(allocations.values()) # Sum the total amount of money distributed
    for name, amount in allocations.items(): # For every category in the results
        categories[name]["budgeted_amount"] = amount # Update the profile with the calculated budget

    return cast( # Return the finalized allocation object
        BudgetAllocation, # The return type
        { # The results dictionary
            "strategy": "50/30/20", # Strategy name
            "allocations": allocations, # Dictionary of category -> dollars
            "categories": categories, # Updated category profiles
            "allocated_total": round(allocated_total, 2), # Total money used
            "remaining": round(income - allocated_total, 2), # Money left over due to rounding
            "warnings": warnings, # Any issues encountered
        }, # End results
    ) # End cast


def allocate_priority_weighted(income: float, categories: dict[str, BudgetCategoryProfile]) -> BudgetAllocation: # Strategy: Priority
    """Distribute the full budget proportionally by priority score.""" # Docstring for priority-based distribution
    if income < 0: # Check for invalid income
        raise ValueError("Income cannot be negative.") # Stop if negative
    categories = deepcopy(categories) # Use a copy to prevent side effects
    allocations: dict[str, float] = {} # Initialize results
    total_priority = 0 # Initialize the denominator
    for info in categories.values(): # Iterate through every category profile
        total_priority += int(info["priority"]) # Sum up the priority scores

    if total_priority == 0: # Check if all priorities were set to zero
        raise ValueError("Priority scores cannot sum to zero.") # Stop if distribution is mathematically impossible

    running_total = 0.0 # Track spending to prevent rounding leaks
    names = list(categories) # Get a fixed list of category names
    for index, name in enumerate(names, start=1): # Iterate through names with index
        if index == len(names): # If this is the last category
            amount = round(income - running_total, 2) # Assign the entire remainder
        else: # For all others
            share = int(categories[name]["priority"]) / total_priority # Calculate the ratio based on priority
            amount = round(income * share, 2) # Calculate the dollar amount
            running_total += amount # Update the running total
        allocations[name] = max(0.0, amount) # Ensure non-negative and store
        categories[name]["budgeted_amount"] = allocations[name] # Update the profile

    return cast( # Return the finalized allocation
        BudgetAllocation, # Type hint
        { # Results dictionary
            "strategy": "Priority Weighted", # Strategy name
            "allocations": allocations, # Resulting dollars
            "categories": categories, # Profiles
            "allocated_total": round(sum(allocations.values()), 2), # Total spent
            "remaining": round(income - sum(allocations.values()), 2), # Leftover
            "warnings": [], # No specific warnings for this strategy
        }, # End results
    ) # End cast


def build_zero_based_suggestion(income: float, categories: dict[str, BudgetCategoryProfile]) -> dict[str, float]: # Helper for Zero-Based
    """Create a suggested zero-based plan when the user is not entering amounts manually.""" # Docstring for the suggestion engine
    ordered_names = sorted( # Sort categories to decide who gets money first
        categories, # The list of names to sort
        key=lambda name: ( # Define complex sorting priority
            TIER_RANK.get(str(categories[name]["tier"]), 99), # First sort by tier (Needs then Wants then Savings)
            -int(categories[name]["priority"]), # Second sort by priority rank (highest first)
            -float(categories[name]["weight"]), # Third sort by weight (highest first)
        ), # End of sort key
    ) # End of sort
    remaining = round(income, 2) # Start with the full income amount
    allocations: dict[str, float] = {} # Initialize results dictionary
    assigned: set[str] = set() # Track who has received money

    total_priority = sum(int(info["priority"]) for info in categories.values()) or 1 # Get a total for initial proportional logic
    for index, name in enumerate(ordered_names, start=1): # Iterate through sorted categories
        if name in assigned: # Skip if already processed
            continue # Go to next
        if index == len(ordered_names): # If this is the last category
            amount = remaining # Give it everything that is left
        else: # For others
            share = int(categories[name]["priority"]) / total_priority # Calculate a priority share
            amount = round(income * share, 2) # Calculate dollar amount
            if amount > remaining: # Check if we have enough money left for this share
                amount = remaining # Cap the amount at the available funds
        allocations[name] = max(0.0, amount) # Store the amount
        remaining = round(remaining - allocations[name], 2) # Subtract from the available pool
        assigned.add(name) # Mark as done

    return allocations # Return the suggested amounts


def allocate_zero_based( # Strategy: Zero-Based Budgeting
    income: float, # Total available funds
    categories: dict[str, BudgetCategoryProfile], # Category profiles
    manual_amounts: dict[str, Any] | None = None, # Optional user-provided amounts
) -> BudgetAllocation: # Returns the final plan
    """Assign every dollar to categories and do not allow overshoot.""" # Docstring for zero-based strategy
    if income < 0: # Check for invalid income
        raise ValueError("Income cannot be negative.") # Stop if negative
    categories = deepcopy(categories) # Copy the data
    allocations: dict[str, float] = {} # Initialize results
    warnings: list[str] = [] # Initialize warnings

    source_amounts = manual_amounts if manual_amounts is not None else build_zero_based_suggestion(income, categories) # Use manual or generated data
    if manual_amounts is not None: # If the user provided specific amounts
        unknown_keys = set(manual_amounts) - set(categories) # Find amounts provided for categories that don't exist
        if unknown_keys: # If there are leftovers
            warnings.append( # Log a warning
                f"Ignored amounts for unknown categories: {', '.join(sorted(unknown_keys))}." # Descriptive message
            ) # End warning
    remaining = round(income, 2) # Start the deduction pool

    for name in categories: # Iterate through all defined categories
        amount = round(float(source_amounts.get(name, 0.0)), 2) # Extract the intended amount
        if amount < 0: # Check for negative input
            raise ValueError("Zero-based budgeting does not allow negative assigned amounts.") # Stop if negative
        if amount > remaining: # Check if the user is trying to spend more than exists
            raise ValueError(f"{name} would overshoot the remaining budget.") # Stop the calculation
        allocations[name] = amount # Store the allocation
        categories[name]["budgeted_amount"] = amount # Update the profile
        remaining = round(remaining - amount, 2) # Subtract from the pool

    if remaining != 0: # Check if money is still unassigned
        warnings.append(f"Zero-based plan left {format_money(remaining)} unassigned.") # Log the leftover amount

    return cast( # Return the finalized object
        BudgetAllocation, # Type hint
        { # Results
            "strategy": "Zero Based", # Strategy name
            "allocations": allocations, # Resulting amounts
            "categories": categories, # Profiles
            "allocated_total": round(sum(allocations.values()), 2), # Total spent
            "remaining": remaining, # Exact remainder
            "warnings": warnings, # List of issues
        }, # End results
    ) # End cast


def compare_strategies(income: float, categories: dict[str, BudgetCategoryProfile]) -> dict[str, BudgetAllocation]: # Analysis function
    """Run all strategy functions so the user can compare them.""" # Docstring for comparison utility
    return { # Return a dictionary containing the results of all strategies
        "50/30/20": allocate_fifty_thirty_twenty(income, categories), # Run standard rule
        "Priority Weighted": allocate_priority_weighted(income, categories), # Run priority rule
        "Zero Based": allocate_zero_based(income, categories), # Run zero-based rule
    } # End of dictionary


def compare_actual_to_budget( # Core analysis function
    allocation: BudgetAllocation, actual_spending: dict[str, Any] # Accept a plan and real data
) -> BudgetComparisonResult: # Return the final report
    """Compare actuals to one budget strategy.

    Includes rows for **actual spending** on names that are not in the allocation
    (budgeted 0, tier ``Unknown``) so unbudgeted spend still appears.
    """ # Detailed docstring for report generation
    alloc = allocation["allocations"] # Access the planned amounts
    cats = allocation["categories"] # Access the profiles
    all_names = sorted(set(alloc) | set(actual_spending.keys())) # Merge budgeted and unbudgeted category names
    rows: list[BudgetComparisonRow] = [] # Initialize report rows
    total_actual = 0.0 # Counter for total real spending
    total_budgeted = 0.0 # Counter for total planned spending
    overages: set[str] = set() # Track which categories went over
    under_budget: set[str] = set() # Track which categories stayed under

    for name in all_names: # Iterate through every category found in either dataset
        budgeted_amount = round(float(alloc.get(name, 0.0)), 2) # Get planned amount or zero
        actual = round(float(actual_spending.get(name, 0.0)), 2) # Get actual amount or zero
        difference = round(actual - budgeted_amount, 2) # Calculate the over/under gap
        total_actual += actual # Update real spend total
        total_budgeted += budgeted_amount # Update planned spend total

        if budgeted_amount == 0: # Check for division by zero
            percentage_of_budget: float | None = None # Set percentage to null if no budget exists
        else: # If a budget exists
            percentage_of_budget = (actual / budgeted_amount) * 100 # Calculate the spend ratio

        if actual > budgeted_amount: # Category is over budget
            status = "OVER" # Set status label
            overages.add(name) # Record the overage
        elif actual < budgeted_amount: # Category is under budget
            status = "UNDER" # Set status label
            under_budget.add(name) # Record the surplus
        else: # Category is exactly on target
            status = "EVEN" # Set status label

        profile = cats.get(name) # Retrieve profile if it exists
        tier = profile["tier"] if profile else "Unknown" # Get tier or use placeholder
        priority = int(profile["priority"]) if profile else 0 # Get priority or use placeholder

        rows.append( # Add the data to the report rows
            cast( # Type hint
                BudgetComparisonRow, # Row schema
                { # Data dictionary
                    "category": name, # Category name
                    "budgeted": round(budgeted_amount, 2), # Planned cents
                    "actual": actual, # Real cents
                    "difference": difference, # The gap
                    "percentage_of_budget": percentage_of_budget, # Spending ratio
                    "status": status, # Over/Under/Even
                    "tier": tier, # Classification
                    "priority": priority, # Importance
                }, # End row
            ) # End cast
        ) # End append

    rows.sort(key=lambda item: (item["status"] != "OVER", -abs(item["difference"]))) # Sort report by overages first, then by largest gap
    return cast( # Return final result
        BudgetComparisonResult, # Schema
        { # Data
            "rows": rows, # List of row objects
            "overages": overages, # Names that went over
            "under_budget": under_budget, # Names that stayed under
            "total_overage": round(sum(max(0.0, row["difference"]) for row in rows), 2), # Sum of all overage amounts
            "total_surplus": round(sum(max(0.0, -row["difference"]) for row in rows), 2), # Sum of all saved money
            "total_actual": round(total_actual, 2), # Total real spending
            "total_budgeted": round(total_budgeted, 2), # Total planned spending
        }, # End data
    ) # End cast


def donor_allowed(overage_row: BudgetComparisonRow, candidate_row: BudgetComparisonRow) -> bool: # Rule engine for redistribution
    """Keep redistribution suggestions inside conservative category rules.""" # Docstring for safety logic
    if candidate_row["status"] != "UNDER": # Only categories with extra money can be candidates
        return False # Reject
    if candidate_row["category"] == overage_row["category"]: # Cannot redistribute money to itself
        return False # Reject
    if candidate_row["tier"] == overage_row["tier"] and candidate_row["priority"] <= overage_row["priority"]: # Allow moving money within same tier if priority is lower
        return True # Approve
    if overage_row["tier"] == "Needs" and candidate_row["tier"] == "Wants": # Allow taking money from Wants to cover essential Needs
        return True # Approve
    return False # Reject all other combinations


def build_redistribution_suggestions(comparison: BudgetComparisonResult) -> list[dict[str, Any]]: # Advice generator
    """Suggest how under-budget categories could absorb overages.""" # Docstring for suggestions
    suggestions: list[dict[str, Any]] = [] # Initialize the advice list
    rows = comparison["rows"] # Access the comparison data
    for overage_row in rows: # Look at every row in the report
        if overage_row["status"] != "OVER": # Only care about categories that are over budget
            continue # Move to next
        needed = overage_row["difference"] # The amount needed to cover the overage
        donors = [] # Initialize a list of categories to take money from
        for candidate_row in rows: # Search for potential donor categories
            if not donor_allowed(overage_row, candidate_row): # Check if the redistribution rule allows it
                continue # Skip this candidate
            available = abs(min(0.0, candidate_row["difference"])) # Calculate how much extra money is in this category
            if available <= 0: # Skip if no surplus exists
                continue # Go to next
            amount = min(needed, available) # Take either what's needed or what's available (whichever is smaller)
            if amount > 0: # If we can take money
                donors.append({"from": candidate_row["category"], "amount": round(amount, 2)}) # Record the transfer
                needed = round(needed - amount, 2) # Reduce the remaining amount needed
            if needed <= 0: # If the overage is fully covered
                break # Stop searching for more donors

        if donors: # If we found ways to fix the overage
            suggestions.append({"category": overage_row["category"], "needed": overage_row["difference"], "donors": donors}) # Record the full advice
    return suggestions # Return the list of suggestions


def menu() -> None: # Delegation function
    """Interactive budget menu delegated to the CLI module.""" # Docstring for menu proxy
    try: # Attempt to find the CLI module
        from .budget_cli import menu as cli_menu # Package-relative import
    except ImportError: # Fallback
        from budget_cli import menu as cli_menu # Direct import
    cli_menu() # Execute the actual interface logic


def main() -> None: # Entry point
    menu() # Launch the menu


if __name__ == "__main__": # Boilerplate to check if script is being run directly
    main() # Call the main function