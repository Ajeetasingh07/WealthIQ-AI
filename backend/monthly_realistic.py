import pandas as pd

# Load realistic transactions
df = pd.read_csv("data/realistic_transactions.csv")

# Convert date
df["date"] = pd.to_datetime(df["date"])

# Keep only expenses
expenses = df[df["type"] == "expense"].copy()

# Create month column
expenses["month"] = expenses["date"].dt.to_period("M").astype(str)

# Calculate monthly spending
monthly = (
    expenses.groupby("month")["amount"]
    .sum()
    .reset_index()
)

# Save result
monthly.to_csv(
    "data/realistic_monthly_spending.csv",
    index=False
)

print("Realistic monthly dataset created!")
print("\nMonthly spending:")
print(monthly)