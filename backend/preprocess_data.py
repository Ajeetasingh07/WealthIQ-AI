import pandas as pd

# Load the larger dataset
df = pd.read_csv("data/wealthiq_transactions.csv")

# Convert date column
df["date"] = pd.to_datetime(df["date"])

# Check missing values
print("Missing values:")
print(df.isnull().sum())

# Check data types
print("\nData types:")
print(df.dtypes)

# Sort transactions by date
df = df.sort_values("date")

# Create month column
df["month"] = df["date"].dt.to_period("M").astype(str)

# Keep only expenses for spending analysis
expenses = df[df["type"] == "expense"].copy()

print("\nTotal transactions:", len(df))
print("Total expenses:", len(expenses))

print("\nExpense data:")
print(expenses.head())

# Save cleaned expense data
expenses.to_csv("data/cleaned_expenses.csv", index=False)

print("\nCleaned dataset saved successfully!")