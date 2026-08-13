import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error

# Load realistic monthly spending
df = pd.read_csv("data/realistic_monthly_spending.csv")

df = df.rename(columns={
    "month": "ds",
    "amount": "y"
})

df["ds"] = pd.to_datetime(df["ds"])

# Use the last 3 months as test data
train = df.iloc[:-3]
test = df.iloc[-3:]

# Create and train model
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False
)

model.fit(train)

# Predict test months
forecast = model.predict(test[["ds"]])

# Compare actual and predicted values
actual = test["y"].values
predicted = forecast["yhat"].values

mae = mean_absolute_error(actual, predicted)

print("\nActual spending:")
print(actual)

print("\nPredicted spending:")
print(predicted)

print("\nMean Absolute Error (MAE):", round(mae, 2))