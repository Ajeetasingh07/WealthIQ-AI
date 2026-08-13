import pandas as pd
from sklearn.metrics import mean_absolute_error

# Load realistic monthly spending
df = pd.read_csv("data/realistic_monthly_spending.csv")

# Use last 3 months for testing
train = df.iloc[:-3].copy()
test = df.iloc[-3:].copy()

# Average spending from training data
average_spending = train["amount"].mean()

# Predict the same average for each test month
predicted = [average_spending] * len(test)

# Actual values
actual = test["amount"].values

# Calculate MAE
mae = mean_absolute_error(actual, predicted)

print("Actual spending:")
print(actual)

print("\nBaseline predictions:")
print(predicted)

print("\nBaseline MAE:", round(mae, 2))