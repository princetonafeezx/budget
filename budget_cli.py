from __future__ import annotations # Enable postponed evaluation of type annotations for forward compatibility

from typing import cast # Import cast to manually override type inference when necessary

try:  # Attempt package-relative imports for when the project is installed as a library
    from . import budget # Import the core budget logic module from the current package
    from .schemas import BudgetAllocation, BudgetCategoryProfile, BudgetComparisonResult # Import data structure definitions
    from .storage import format_money # Import currency formatting utility from the storage module
except ImportError:  # Fallback for when the script is executed directly from the command line
    import budget # Import the local budget logic file
    from schemas import BudgetAllocation, BudgetCategoryProfile, BudgetComparisonResult # Import schemas from the local directory
    from storage import format_money # Import storage utilities from the local directory


def print_allocation_table(allocation: BudgetAllocation) -> None: # Define a function to display a specific budget plan in a table
    print(f"{allocation['strategy']} allocation") # Print the name of the budgeting strategy used
    print(f"{'Category':<18}{'Tier':<10}{'Weight':>8}{'Budgeted':>16}") # Print the table headers with specific column widths
    print("-" * 52) # Print a separator line for visual clarity
    for name, info in allocation["categories"].items(): # Iterate through each category and its configuration metadata
        amount = format_money(allocation["allocations"].get(name, 0.0)) # Format the calculated budget amount as currency
        print(f"{name:<18}{info['tier']:<10}{info['weight']:>8}{amount:>16}") # Print the row data aligned with the headers
    print("-" * 52) # Print a bottom separator line
    print(f"Allocated total: {format_money(allocation['allocated_total'])}") # Show the total sum of money distributed
    print(f"Remaining: {format_money(allocation['remaining'])}") # Show any leftover income that wasn't allocated
    for warning in allocation["warnings"]: # Check for any logic warnings generated during allocation
        print(f"Warning: {warning}") # Display the warning message to the user


def print_strategy_comparison_table(results: dict[str, BudgetAllocation]) -> None: # Define a function to compare multiple strategies side-by-side
    if not results: # Check if the results dictionary is empty
        print("No strategies to compare.") # Inform the user if no data is available
        return # Exit the function early
    categories = list(next(iter(results.values()))["categories"]) # Extract the list of category names from the first result
    header = f"{'Category':<18}" # Initialize the header string with the first column label
    for strategy_name in results: # Loop through each strategy name in the results
        header += f"{strategy_name[:16]:>18}" # Append truncated strategy names to the header row
    print(header) # Display the completed header row
    print("-" * len(header)) # Print a separator line equal to the header width
    for category in categories: # Iterate through each budget category
        line = f"{category:<18}" # Start a new row with the category name
        for _strategy_name, result in results.items(): # Loop through each strategy result for the current category
            line += f"{format_money(result['allocations'].get(category, 0.0)):>18}" # Append the allocated amount for that strategy
        print(line) # Print the completed comparison row


def print_comparison_report(comparison: BudgetComparisonResult, income: float) -> None: # Define a function to show budget vs. actual spending
    print(f"{'Category':<18}{'Budgeted':>14}{'Actual':>14}{'Difference':>14}{'Status':>10}") # Print column headers for the report
    print("-" * 70) # Print a wide separator line
    for row in comparison["rows"]: # Iterate through each row of the comparison data
        marker = "**" if row["status"] == "OVER" else "" # Add a visual marker if the category is over budget
        pct = row["percentage_of_budget"] # Get the percentage of the budget spent
        detail = f"{pct:.0f}%" if pct is not None else "n/a" # Format the percentage or use 'n/a' if invalid
        print( # Use f-string to print a formatted line of the report
            f"{row['category']:<18}" # Category name
            f"{format_money(row['budgeted']):>14}" # Planned amount
            f"{format_money(row['actual']):>14}" # Real spending
            f"{format_money(row['difference']):>14}" # Difference between the two
            f"{(marker + row['status'] + ' ' + detail):>10}" # Status label and percentage
        ) # End of the row print

    print("-" * 70) # Print a bottom separator line
    print(f"Total income: {format_money(income)}") # Display the original monthly income
    print(f"Total budgeted: {format_money(comparison['total_budgeted'])}") # Display the total planned spending
    print(f"Total spent: {format_money(comparison['total_actual'])}") # Display the total actual spending
    print(f"Total overage: {format_money(comparison['total_overage'])}") # Display the sum of all over-budget amounts
    print(f"Total surplus: {format_money(comparison['total_surplus'])}") # Display the sum of all under-budget amounts

    suggestions = budget.build_redistribution_suggestions(comparison) # Generate smart suggestions to fix overages
    if suggestions: # Check if any suggestions were created
        print() # Print a blank line for spacing
        print("Redistribution suggestions") # Header for the suggestions section
        for suggestion in suggestions: # Iterate through each fix-it suggestion
            donor_text = ", ".join(f"{item['from']} {format_money(item['amount'])}" for item in suggestion["donors"]) # Format the list of sources
            print(f"{suggestion['category']} could absorb {format_money(suggestion['needed'])} from {donor_text}") # Print the final advice


def prompt_float(prompt: str, allow_zero: bool = True) -> float | None: # Define a utility for safe numeric user input
    entered = input(prompt).strip() # Get input from the user and remove surrounding spaces
    try: # Attempt to convert input to a number
        value = float(entered) # Convert string to float
    except ValueError: # Handle cases where input is not a valid number
        print("Please enter a numeric value.") # Inform the user of the error
        return None # Return None to signify a failed attempt
    if value < 0: # Check if the number is negative
        print("Negative values are not allowed here.") # Inform the user negative numbers are invalid
        return None # Return None to signify a failed attempt
    if value == 0 and not allow_zero: # Check if zero is allowed for this specific field
        print("Zero is not allowed for this field.") # Inform the user zero is invalid
        return None # Return None to signify a failed attempt
    return value # Return the valid float value


def add_category(categories: dict[str, BudgetCategoryProfile]) -> None: # Define a function to add a new category to the budget
    existing: set[str] = set(categories) # Create a set of existing names to check for duplicates
    name = input("Category name: ").strip() # Prompt for the new category name
    tier = input("Tier (Needs/Wants/Savings): ").strip().title() # Prompt for the tier and capitalize it
    weight = input("Weight: ").strip() # Prompt for the weight (multiplier)
    priority = input("Priority 1-10: ").strip() # Prompt for the priority ranking
    try: # Attempt to build a new profile dictionary
        info = {"tier": tier, "weight": float(weight), "priority": int(priority), "actual_spend": 0.0, "budgeted_amount": 0.0} # Create the profile
    except ValueError: # Handle cases where numeric inputs are invalid
        print("Weight and priority have to be numeric.") # Inform the user of the requirement
        return # Exit the function
    errors = budget.validate_category(name, info, existing) # Run logical validation against the new data
    if errors: # If validation errors are found
        for error in errors: # Loop through each error
            print(error) # Print the error message
        return # Stop the addition process
    categories[name] = cast(BudgetCategoryProfile, info) # Save the new category into the main dictionary
    print(f"Added {name}.") # Confirm successful addition


def edit_category(categories: dict[str, BudgetCategoryProfile]) -> None: # Define a function to modify an existing category
    name = input("Category to edit: ").strip() # Prompt for the name of the category to change
    if name not in categories: # Check if the category exists
        print("That category was not found.") # Inform the user if it's missing
        return # Exit the function
    info = categories[name] # Retrieve the current profile data
    new_tier = input(f"Tier [{info['tier']}]: ").strip().title() or info["tier"] # Prompt for new tier, defaulting to current if blank
    new_weight_text = input(f"Weight [{info['weight']}]: ").strip() # Prompt for new weight
    new_priority_text = input(f"Priority [{info['priority']}]: ").strip() # Prompt for new priority
    try: # Attempt to update the values while maintaining numeric types
        updated = { # Create an updated dictionary
            "tier": new_tier, # Set the new tier
            "weight": float(new_weight_text) if new_weight_text else float(info["weight"]), # Update weight if provided
            "priority": int(new_priority_text) if new_priority_text else int(info["priority"]), # Update priority if provided
            "actual_spend": float(info["actual_spend"]), # Maintain current actual spend
            "budgeted_amount": float(info["budgeted_amount"]), # Maintain current budgeted amount
        } # End of dictionary update
    except ValueError: # Handle cases where user input is not a number
        print("Weight and priority have to stay numeric.") # Inform the user
        return # Exit the function
    errors = budget.validate_category(name, updated, set(categories) - {name}) # Validate changes against other categories
    if errors: # If errors occur during validation
        for error in errors: # Loop through errors
            print(error) # Display error
        return # Stop the update
    categories[name] = cast(BudgetCategoryProfile, updated) # Save the changes
    print(f"Updated {name}.") # Confirm successful update


def remove_category(categories: dict[str, BudgetCategoryProfile]) -> None: # Define a function to delete a category
    name = input("Category to remove: ").strip() # Prompt for the category name to delete
    if name in categories: # Check if the name is in the budget
        categories.pop(name) # Remove the item from the dictionary
        print(f"Removed {name}.") # Confirm removal
    else: # If the name is not found
        print("That category was not found.") # Inform the user


def enter_actual_spending(categories: dict[str, BudgetCategoryProfile]) -> dict[str, float]: # Function to collect real-world spend data
    actuals: dict[str, float] = {} # Initialize a dictionary to store spending amounts
    for name in categories: # Iterate through every category in the budget
        entered = input(f"Actual spending for {name} [0]: ").strip() # Prompt user for spend amount
        if not entered: # If user hits enter without typing
            actuals[name] = 0.0 # Default the spend to zero
            continue # Move to the next category
        try: # Attempt to process the input number
            amount = float(entered) # Convert to float
            if amount < 0: # Disallow negative spending
                print("Negative actual spending is not allowed, so I used 0 instead.") # Inform user of correction
                amount = 0.0 # Reset to zero
            actuals[name] = amount # Store the valid amount
        except ValueError: # Handle invalid text input
            print("That number was invalid, so I used 0 instead.") # Inform user of correction
            actuals[name] = 0.0 # Default to zero
    return actuals # Return the completed spending dictionary


def menu() -> None: # Main entry point for the interactive CLI
    """Interactive budget menu.""" # Function docstring
    income = 0.0 # Initialize monthly income to zero
    categories = budget.starter_categories() # Load a set of default categories to begin with
    actual_spending: dict[str, float] = {} # Initialize empty spending tracking
    last_allocation: BudgetAllocation | None = None # Track the most recent budget plan for comparisons
    valid_choices = {"1", "2", "3", "4", "5", "6"} # Define the set of allowed menu inputs

    while True: # Start an infinite loop to keep the program running
        print() # Print blank line for spacing
        print("LedgerLogic: Priority-Based Budget Distributor") # Application title
        print("1. Set income") # Option to define monthly funds
        print("2. Manage categories") # Option to add/edit/remove categories
        print("3. Run a strategy") # Option to calculate a specific budget plan
        print("4. Run all strategies and compare") # Option to see side-by-side results
        print("5. Enter actual spending / view comparison") # Option to check budget vs. reality
        print("6. Quit") # Option to close the program
        choice = input("Choose an option: ").strip() # Get the user's menu choice
        if choice not in valid_choices: # Validate the choice
            print("Please choose a valid menu number.") # Error message for invalid choice
            continue # Restart the loop

        if choice == "1": # Handle income setup
            new_income = prompt_float("Monthly income: ", allow_zero=True) # Prompt for income amount
            if new_income is not None: # If a valid number was returned
                income = new_income # Update the income variable
                print(f"Income is now {format_money(income)}.") # Confirm the new income setting

        elif choice == "2": # Handle category management submenu
            print("a. Add category") # Sub-option for addition
            print("b. Edit category") # Sub-option for editing
            print("c. Remove category") # Sub-option for deletion
            print("d. View categories") # Sub-option for listing current state
            sub = input("Choice: ").strip().lower() # Get the sub-option choice
            if sub == "a": # If user wants to add
                add_category(categories) # Call the add function
            elif sub == "b": # If user wants to edit
                edit_category(categories) # Call the edit function
            elif sub == "c": # If user wants to remove
                remove_category(categories) # Call the remove function
            elif sub == "d": # If user wants to see current list
                for name, info in categories.items(): # Loop through categories
                    print(f"{name:<18}{info['tier']:<10}{info['weight']:>6}{info['priority']:>6}") # Print formatted row
            else: # If sub-option is unrecognized
                print("That category option was not recognized.") # Inform the user

        elif choice == "3": # Handle running a specific budget strategy
            if not categories: # Check if any categories exist
                print("Please add at least one category first.") # Inform the user categories are required
                continue # Restart the loop
            if income == 0: # Check if income has been set
                print("Income is zero, so the plan will be all zeros unless you change it.") # Warning about zero income
            print("a. 50/30/20") # Sub-option for standard rule
            print("b. Priority weighted") # Sub-option for custom weights
            print("c. Zero based") # Sub-option for zero-based budgeting
            sub = input("Strategy: ").strip().lower() # Get the strategy choice
            try: # Attempt to run the chosen strategy
                if sub == "a": # If 50/30/20
                    last_allocation = budget.allocate_fifty_thirty_twenty(income, categories) # Run the rule
                elif sub == "b": # If Priority Weighted
                    last_allocation = budget.allocate_priority_weighted(income, categories) # Run the custom logic
                elif sub == "c": # If Zero Based
                    last_allocation = budget.allocate_zero_based(income, categories) # Run zero-based logic
                else: # If strategy key is wrong
                    print("That strategy key was not recognized.") # Inform the user
                    continue # Restart loop
                print_allocation_table(last_allocation) # Display the resulting plan
            except ValueError as error: # Handle mathematical or logical errors during allocation
                print(f"Could not run strategy: {error}") # Display error to user

        elif choice == "4": # Handle multi-strategy comparison
            if not categories: # Check for categories
                print("Please add categories first.") # Inform the user
                continue # Restart loop
            try: # Attempt to run and compare all available strategies
                results = budget.compare_strategies(income, categories) # Run the comparison logic
                print_strategy_comparison_table(results) # Display the side-by-side table
            except ValueError as error: # Handle errors during comparison
                print(f"Could not compare strategies: {error}") # Display error

        elif choice == "5": # Handle actual spending and report generation
            if last_allocation is None: # Check if a budget has been calculated yet
                print("Run a strategy first so there is a budget to compare against.") # Inform user of prerequisite
                continue # Restart loop
            actual_spending = enter_actual_spending(categories) # Prompt for all spending values
            comparison = budget.compare_actual_to_budget(last_allocation, actual_spending) # Run the comparison analysis
            print_comparison_report(comparison, income) # Display the final spending report

        elif choice == "6": # Handle program exit
            print("Exiting budget allocator.") # Farewall message
            break # Break the infinite loop to exit