from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

DATA_FILE = "data/realistic_transactions.csv"


@app.route("/")
def home():
    return jsonify({
        "project": "WealthIQ AI",
        "status": "running",
        "message": "WealthIQ AI backend is working!"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/transactions")
def transactions():
    df = pd.read_csv(DATA_FILE)

    return jsonify(
        df.to_dict(orient="records")
    )


@app.route("/forecast")
def forecast():
    forecast_df = pd.read_csv(
        "data/realistic_spending_forecast.csv"
    )

    result = forecast_df[
        ["ds", "yhat", "yhat_lower", "yhat_upper"]
    ]

    return jsonify(
        result.to_dict(orient="records")
    )
@app.route("/budget")
def budget():
    forecast_df = pd.read_csv(
        "data/realistic_spending_forecast.csv"
    )

    predicted_spending = forecast_df.iloc[0]["yhat"]

    monthly_income = 48000

    safety_buffer = monthly_income * 0.10

    recommended_budget = monthly_income - safety_buffer

    estimated_remaining = monthly_income - predicted_spending

    if predicted_spending > recommended_budget:
        status = "warning"
    else:
        status = "within_budget"

    return jsonify({
        "monthly_income": monthly_income,
        "predicted_spending": round(predicted_spending, 2),
        "recommended_budget": round(recommended_budget, 2),
        "estimated_remaining": round(estimated_remaining, 2),
        "status": status
    })
@app.route("/dashboard")
def dashboard():

    # Load transactions
    df = pd.read_csv(DATA_FILE)

    # Calculate income
    total_income = df[df["type"] == "income"]["amount"].sum()

    # Calculate expenses
    expenses = df[df["type"] == "expense"]

    total_expenses = expenses["amount"].sum()

    # Calculate balance
    balance = total_income - total_expenses

    # Calculate spending by category
    category_spending = (
        expenses.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    top_category = str(category_spending.idxmax())
    top_category_amount = float(category_spending.max())

    # Load forecast
    forecast_df = pd.read_csv(
        "data/realistic_spending_forecast.csv"
    )

    predicted_spending = float(
        forecast_df.iloc[0]["yhat"]
    )

    # Budget
    monthly_income = 48000
    recommended_budget = monthly_income * 0.90

    if predicted_spending > recommended_budget:
        budget_status = "warning"
    else:
        budget_status = "within_budget"

    return jsonify({
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "balance": float(balance),
        "predicted_spending": round(predicted_spending, 2),
        "top_category": top_category,
        "top_category_amount": round(top_category_amount, 2),
        "recommended_budget": round(recommended_budget, 2),
        "budget_status": budget_status
    })
if __name__ == "__main__":
    app.run(debug=True)