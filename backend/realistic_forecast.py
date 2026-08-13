import pandas as pd
from prophet import Prophet

# Load realistic monthly spending
df = pd.read_csv("data/realistic_monthly_spending.csv")

# Rename columns for Prophet
df = df.rename(columns={
    "month": "ds",
    "amount": "y"
})

# Convert date
df["ds"] = pd.to_datetime(df["ds"])

# Create Prophet model
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False
)

# Train model
model.fit(df)

# Predict next 6 months
future = model.make_future_dataframe(
    periods=6,
    freq="MS"
)

forecast = model.predict(future)

# Show future predictions
future_forecast = forecast[
    ["ds", "yhat", "yhat_lower", "yhat_upper"]
].tail(6)

print("\nPredicted Future Spending:")
print(future_forecast)

# Save predictions
future_forecast.to_csv(
    "data/realistic_spending_forecast.csv",
    index=False
)

print("\nRealistic forecast saved successfully!")
