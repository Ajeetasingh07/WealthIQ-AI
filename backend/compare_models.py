import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error

# Load data
df = pd.read_csv("data/realistic_monthly_spending.csv")

df = df.rename(columns={
    "month": "ds",
    "amount": "y"
})

df["ds"] = pd.to_datetime(df["ds"])

# Split data
train = df.iloc[:-3]
test = df.iloc[-3:]

# -------------------------
# Baseline Model
# -------------------------

baseline_prediction = [train["y"].mean()] * len(test)

baseline_mae = mean_absolute_error(
    test["y"],
    baseline_prediction
)

# -------------------------
# Prophet Model
# -------------------------

model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False
)

model.fit(train)

forecast = model.predict(test[["ds"]])

prophet_prediction = forecast["yhat"].values

prophet_mae = mean_absolute_error(
    test["y"],
    prophet_prediction
)

# -------------------------
# Results
# -------------------------

print("\nModel Comparison")
print("------------------------")

print(
    "Baseline MAE:",
    round(baseline_mae, 2)
)

print(
    "Prophet MAE:",
    round(prophet_mae, 2)
)

if prophet_mae < baseline_mae:
    print("\nProphet performed better.")
else:
    print("\nBaseline performed better.")