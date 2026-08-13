import pandas as pd

# Load realistic transactions
df = pd.read_csv("data/realistic_transactions.csv")

# Keep only expenses
expenses = df[df["type"] == "expense"].copy()

# Calculate spending by category
category_spending = (
    expenses.groupby("category")["amount"]
    .sum()
    .sort_values(ascending=False)
)

print("\nWEALTHIQ CATEGORY ANALYSIS")
print("--------------------------")

print(category_spending)

# Find highest spending category
top_category = category_spending.idxmax()
top_amount = category_spending.max()

print("\nHighest spending category:")
print(f"{top_category} — ₹{top_amount:,.2f}")

# Calculate percentage
total_spending = category_spending.sum()

percentage = (top_amount / total_spending) * 100

print(
    f"Percentage of total spending: {percentage:.2f}%"
)

# Simple recommendation
print("\nWEALTHIQ INSIGHT")

if percentage > 30:
    print(
        f"⚠️ {top_category} is taking a large portion "
        "of your total spending."
    )
else:
    print(
        f"✅ Your spending is relatively distributed, "
        f"but {top_category} is your largest category."
    )