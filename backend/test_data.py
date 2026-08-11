import pandas as pd

# Load data
df = pd.read_csv("data/transactions.csv")

# Convert date to datetime
df["date"] = pd.to_datetime(df["date"])

# Categorize transactions
def categorize(merchant):
    merchant = merchant.lower()

    if "amazon" in merchant:
        return "Shopping"
    elif "netflix" in merchant:
        return "Entertainment"
    elif "swiggy" in merchant:
        return "Food"
    elif "electricity" in merchant:
        return "Bills"
    elif "uber" in merchant:
        return "Transport"
    elif "salary" in merchant:
        return "Income"
    else:
        return "Other"


df["category"] = df["merchant"].apply(categorize)

# Create month column
df["month"] = df["date"].dt.to_period("M")

# Monthly income
monthly_income = (
    df[df["type"] == "income"]
    .groupby("month")["amount"]
    .sum()
)

# Monthly expenses
monthly_expense = (
    df[df["type"] == "expense"]
    .groupby("month")["amount"]
    .sum()
)

print("\nMonthly Income:")
print(monthly_income)

print("\nMonthly Expenses:")
print(monthly_expense)