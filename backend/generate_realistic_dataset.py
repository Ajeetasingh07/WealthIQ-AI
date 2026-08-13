import pandas as pd
import random
from datetime import datetime

random.seed(42)

transactions = []

# Generate 24 months of data
months = pd.date_range("2024-07-01", "2026-06-01", freq="MS")

for month in months:

    year = month.year
    m = month.month

    # -------------------------
    # Monthly Salary
    # -------------------------
    salary = 45000

    if year == 2026:
        salary = 48000

    transactions.append({
        "date": month.strftime("%Y-%m-%d"),
        "merchant": "Salary",
        "amount": salary,
        "type": "income",
        "category": "Income"
    })

    # -------------------------
    # Rent
    # -------------------------
    transactions.append({
        "date": f"{year}-{m:02d}-05",
        "merchant": "Rent",
        "amount": 12000,
        "type": "expense",
        "category": "Housing"
    })

    # -------------------------
    # Electricity
    # -------------------------
    electricity = random.randint(1200, 2200)

    transactions.append({
        "date": f"{year}-{m:02d}-10",
        "merchant": "Electricity Bill",
        "amount": electricity,
        "type": "expense",
        "category": "Bills"
    })

    # -------------------------
    # Internet
    # -------------------------
    transactions.append({
        "date": f"{year}-{m:02d}-12",
        "merchant": "Internet Bill",
        "amount": 799,
        "type": "expense",
        "category": "Bills"
    })

    # -------------------------
    # Netflix subscription
    # -------------------------
    transactions.append({
        "date": f"{year}-{m:02d}-15",
        "merchant": "Netflix",
        "amount": 649,
        "type": "expense",
        "category": "Entertainment"
    })

    # -------------------------
    # Food spending
    # -------------------------
    for i in range(5):
        day = random.randint(3, 27)

        amount = random.randint(300, 900)

        # Slightly higher food spending
        # during festive months
        if m in [10, 11, 12]:
            amount += random.randint(100, 400)

        transactions.append({
            "date": f"{year}-{m:02d}-{day:02d}",
            "merchant": random.choice(
                ["Swiggy", "Zomato", "Dominos"]
            ),
            "amount": amount,
            "type": "expense",
            "category": "Food"
        })

    # -------------------------
    # Shopping
    # -------------------------
    shopping_amount = random.randint(1500, 4000)

    if m in [10, 11]:
        shopping_amount += 3000

    transactions.append({
        "date": f"{year}-{m:02d}-20",
        "merchant": random.choice(
            ["Amazon", "Flipkart", "Myntra"]
        ),
        "amount": shopping_amount,
        "type": "expense",
        "category": "Shopping"
    })

    # -------------------------
    # Transport
    # -------------------------
    for i in range(4):
        day = random.randint(4, 26)

        transactions.append({
            "date": f"{year}-{m:02d}-{day:02d}",
            "merchant": random.choice(
                ["Uber", "Ola", "Metro"]
            ),
            "amount": random.randint(150, 600),
            "type": "expense",
            "category": "Transport"
        })


df = pd.DataFrame(transactions)

df = df.sort_values("date")

df.to_csv(
    "data/realistic_transactions.csv",
    index=False
)

print("Realistic dataset created successfully!")
print("Total transactions:", len(df))

print("\nDate range:")
print(df["date"].min(), "to", df["date"].max())

print("\nCategory distribution:")
print(df["category"].value_counts())

print("\nFirst 10 transactions:")
print(df.head(10))