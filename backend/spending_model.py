import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os

# Project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Dataset path
DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "realistic_monthly_spending.csv"
)

# Model output path
MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "spending_model.pkl"
)

# Load data
df = pd.read_csv(DATA_PATH)

# Convert month to datetime
df["month"] = pd.to_datetime(df["month"])

# Sort chronologically
df = df.sort_values("month").reset_index(drop=True)

# Create time feature
df["time_index"] = np.arange(len(df))

# Features and target
X = df[["time_index"]]
y = df["amount"]

# Train model
model = LinearRegression()
model.fit(X, y)

# Save model
os.makedirs(
    os.path.dirname(MODEL_PATH),
    exist_ok=True
)

joblib.dump(model, MODEL_PATH)

print("Model trained successfully!")
print(f"Training samples: {len(df)}")
print(f"Model saved at: {MODEL_PATH}")

# Predict next 6 months
future_indices = np.arange(
    len(df),
    len(df) + 6
).reshape(-1, 1)

predictions = model.predict(future_indices)

print("\nPredicted spending:")

for i, prediction in enumerate(predictions, start=1):
    print(
        f"Month +{i}: ₹{prediction:,.2f}"
    )