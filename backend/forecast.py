import pandas as pd
from prophet import Prophet

# Load monthly spending data
df = pd.read_csv("data/monthly_spending.csv")

# Prophet requires columns named ds and y
df = df.rename(columns={
    "month": "ds",
    "amount": "y"
})

# Convert date column
df["ds"] = pd.to_datetime(df["ds"])

# Create the forecasting model
model = Prophet()

# Train the model
model.fit(df)

# Create future dates
future = model.make_future_dataframe(
    periods=6,
    freq="MS"
)

# Generate forecast
forecast = model.predict(future)

# Display future predictions
future_forecast = forecast[
    ["ds", "yhat", "yhat_lower", "yhat_upper"]
].tail(6)

print("\nPredicted Monthly Spending:")
print(future_forecast)

# Save forecast
future_forecast.to_csv(
    "data/spending_forecast.csv",
    index=False
)

print("\nForecast saved successfully!")