import pandas as pd

# Load forecast
forecast = pd.read_csv(
    "data/realistic_spending_forecast.csv"
)

# Get the first predicted month
predicted_spending = forecast.iloc[0]["yhat"]

# Example monthly income
monthly_income = 48000

# Create a small safety buffer
safety_buffer = monthly_income * 0.10

# Recommended spending budget
recommended_budget = monthly_income - safety_buffer

# Estimated remaining money
estimated_remaining = monthly_income - predicted_spending

print("WEALTHIQ BUDGET RECOMMENDATION")
print("--------------------------------")

print(
    f"Monthly income: ₹{monthly_income:,.2f}"
)

print(
    f"Predicted spending: ₹{predicted_spending:,.2f}"
)

print(
    f"Recommended spending limit: ₹{recommended_budget:,.2f}"
)

print(
    f"Estimated remaining money: ₹{estimated_remaining:,.2f}"
)

if predicted_spending > recommended_budget:
    print("\n⚠️ Warning: Predicted spending is above the recommended budget.")
else:
    print("\n✅ Spending is within the recommended budget.")

# Savings recommendation
if estimated_remaining > 0:
    print(
        f"💰 Potential savings: ₹{estimated_remaining:,.2f}"
    )
else:
    print("⚠️ Potential cash-flow shortage detected.")