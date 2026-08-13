import pandas as pd

# Load cleaned expense data
df = pd.read_csv("data/cleaned_expenses.csv")

# Convert date
df["date"] = pd.to_datetime(df["date"])

# Create month column
df["month"] = df["date"].dt.to_period("M").astype(str)

# Calculate total spending for each month
monthly_spending = (
    df.groupby("month")["amount"]
    .sum()
    .reset_index()
)

print("Monthly Spending:")
print(monthly_spending)

# Save monthly data
monthly_spending.to_csv(
    "data/monthly_spending.csv",
    index=False
)

print("\nMonthly spending dataset saved successfully!")