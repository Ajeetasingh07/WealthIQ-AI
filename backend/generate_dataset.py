import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

start_date = datetime(2025, 1, 1)
end_date = datetime(2026, 6, 30)

merchants = {
    "Food": ["Swiggy", "Zomato", "Dominos"],
    "Shopping": ["Amazon", "Flipkart", "Myntra"],
    "Transport": ["Uber", "Ola", "Metro"],
    "Entertainment": ["Netflix", "Spotify", "BookMyShow"],
    "Bills": ["Electricity Bill", "Mobile Bill", "Internet Bill"],
}

transactions = []

current_date = start_date

while current_date <= end_date:

    # Monthly salary
    if current_date.day == 1:
        transactions.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "merchant": "Salary",
            "amount": 45000,
            "type": "income",
            "category": "Income"
        })

    # Daily/regular expenses
    if random.random() < 0.35:
        category = random.choice(list(merchants.keys()))
        merchant = random.choice(merchants[category])

        amount_ranges = {
            "Food": (150, 1000),
            "Shopping": (300, 5000),
            "Transport": (100, 800),
            "Entertainment": (200, 1500),
            "Bills": (500, 3000)
        }

        low, high = amount_ranges[category]
        amount = random.randint(low, high)

        transactions.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "merchant": merchant,
            "amount": amount,
            "type": "expense",
            "category": category
        })

    current_date += timedelta(days=1)

df = pd.DataFrame(transactions)

df.to_csv("data/wealthiq_transactions.csv", index=False)

print("Dataset created successfully!")
print("Number of transactions:", len(df))
print("\nFirst 10 transactions:")
print(df.head(10))