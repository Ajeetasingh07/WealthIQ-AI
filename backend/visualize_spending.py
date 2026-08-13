import pandas as pd
import matplotlib.pyplot as plt

# Load monthly spending data
df = pd.read_csv("data/monthly_spending.csv")

# Create the chart
plt.figure(figsize=(12, 6))

plt.plot(
    df["month"],
    df["amount"],
    marker="o"
)

plt.title("WealthIQ Monthly Spending")
plt.xlabel("Month")
plt.ylabel("Total Spending (₹)")

plt.xticks(rotation=45)
plt.tight_layout()

plt.show()