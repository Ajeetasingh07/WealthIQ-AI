import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error

# Load monthly spending data
df = pd.read_csv("data/monthly_spending.csv")

df = df.rename(columns={
    "month": "ds",
    "amount": "y"
})

df["ds"] = pd.to_datetime(df["ds"])

# Keep the last 3 months for testing
train = df.iloc[:-3]
test = df.iloc[-3:]

# Train Prophet
model = Prophet()
model.fit(train)

# Predict the test months
forecast = model.predict(test[["ds"]])

# Compare actual vs predicted
actual = test["y"].values
predicted = forecast["yhat"].values

mae = mean_absolute_error(actual, predicted)

print("Actual spending:")
print(actual)

print("\nPredicted spending:")
print(predicted)

print("\nMean Absolute Error (MAE):", round(mae, 2))