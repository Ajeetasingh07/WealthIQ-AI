from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# DATA FILE
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "transactions.csv"
)


# ============================================================
# LOAD DATA
# ============================================================
def load_data():

    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Automatically create category
    # if the dataset does not contain one
    if "category" not in df.columns:

        def assign_category(merchant):

            merchant = str(merchant).lower()

            if merchant in ["swiggy", "zomato", "dominos"]:
                return "Food"

            elif merchant in ["amazon", "flipkart", "myntra"]:
                return "Shopping"

            elif merchant in ["uber", "ola"]:
                return "Transport"

            elif merchant in ["netflix", "spotify"]:
                return "Entertainment"

            elif merchant in ["electricity", "water", "gas"]:
                return "Bills"

            elif merchant in ["rent", "housing"]:
                return "Housing"

            elif merchant == "salary":
                return "Income"

            else:
                return "Other"

        df["category"] = df["merchant"].apply(
            assign_category
        )

    return df


# ============================================================
# HOME / HEALTH CHECK
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "message": "WealthIQ AI backend is working!",
        "project": "WealthIQ AI",
        "status": "running"
    })


# ============================================================
# DASHBOARD API
# ============================================================

@app.route("/dashboard")
def dashboard():

    df = load_data()

    # Separate income and expenses
    income_df = df[df["type"] == "income"]

    expense_df = df[df["type"] == "expense"]

    # Total income
    total_income = float(
        income_df["amount"].sum()
    )

    # Total expenses
    total_expenses = float(
        expense_df["amount"].sum()
    )

    # Balance
    balance = float(
        total_income - total_expenses
    )

    # --------------------------------------------------------
    # Top category
    # --------------------------------------------------------

    if len(expense_df) > 0:

        category_totals = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        top_category = str(
            category_totals.index[0]
        )

        top_category_amount = float(
            category_totals.iloc[0]
        )

    else:

        top_category = "None"
        top_category_amount = 0.0


    # --------------------------------------------------------
    # Predicted spending
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(df["date"])

    expense_df = df[
        df["type"] == "expense"
    ].copy()

    if len(expense_df) > 0:

        expense_df["month"] = (
            expense_df["date"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly_spending = (
            expense_df
            .groupby("month")["amount"]
            .sum()
            .sort_index()
        )

        if len(monthly_spending) >= 3:

            predicted_spending = float(
                monthly_spending
                .tail(3)
                .mean()
            )

        elif len(monthly_spending) > 0:

            predicted_spending = float(
                monthly_spending.mean()
            )

        else:

            predicted_spending = 0.0

    else:

        predicted_spending = 0.0


    # --------------------------------------------------------
    # Recommended budget
    # --------------------------------------------------------

    recommended_budget = float(
        predicted_spending * 1.10
    )


    # --------------------------------------------------------
    # Budget status
    # --------------------------------------------------------

    if balance >= recommended_budget:

        budget_status = "Healthy"

    elif balance >= 0:

        budget_status = "Needs Attention"

    else:

        budget_status = "Overspending"


    # --------------------------------------------------------
    # JSON response
    # --------------------------------------------------------

    return jsonify({

        "total_income": total_income,

        "total_expenses": total_expenses,

        "balance": balance,

        "predicted_spending": predicted_spending,

        "recommended_budget": recommended_budget,

        "budget_status": budget_status,

        "top_category": top_category,

        "top_category_amount": top_category_amount

    })


# ============================================================
# CATEGORY SPENDING API
# ============================================================

@app.route("/categories")
def categories():

    df = load_data()

    expenses = df[
        df["type"] == "expense"
    ]

    category_spending = (
        expenses
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    return jsonify({

        "categories":
            category_spending
            .index
            .tolist(),

        "amounts":
            category_spending
            .values
            .astype(float)
            .tolist()

    })


# ============================================================
# MONTHLY SPENDING API
# ============================================================

@app.route("/monthly-spending")
def monthly_spending():

    df = load_data()

    df["date"] = pd.to_datetime(
        df["date"]
    )

    expenses = df[
        df["type"] == "expense"
    ].copy()

    expenses["month"] = (
        expenses["date"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly = (
        expenses
        .groupby("month")["amount"]
        .sum()
        .sort_index()
    )

    return jsonify({

        "months":
            monthly
            .index
            .tolist(),

        "amounts":
            monthly
            .values
            .astype(float)
            .tolist()

    })


# ============================================================
# AI FINANCIAL INSIGHTS API
# ============================================================

@app.route("/insights")
def insights():

    df = load_data()

    expenses = df[
        df["type"] == "expense"
    ].copy()

    # --------------------------------------------------------
    # Total spending
    # --------------------------------------------------------

    total_spending = float(
        expenses["amount"].sum()
    )


    # --------------------------------------------------------
    # Top category
    # --------------------------------------------------------

    if len(expenses) > 0:

        category_totals = (
            expenses
            .groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        top_category = str(
            category_totals.index[0]
        )

        top_category_amount = float(
            category_totals.iloc[0]
        )

    else:

        top_category = "None"
        top_category_amount = 0.0


    # --------------------------------------------------------
    # Monthly spending
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"]
    )

    expenses["date"] = pd.to_datetime(
        expenses["date"]
    )

    expenses["month"] = (
        expenses["date"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly = (
        expenses
        .groupby("month")["amount"]
        .sum()
        .sort_index()
    )


    # --------------------------------------------------------
    # Spending trend
    # --------------------------------------------------------

    if len(monthly) >= 2:

        previous_month = float(
            monthly.iloc[-2]
        )

        latest_month = float(
            monthly.iloc[-1]
        )

        if latest_month > previous_month:

            spending_trend = "Increasing"

        elif latest_month < previous_month:

            spending_trend = "Decreasing"

        else:

            spending_trend = "Stable"

    else:

        spending_trend = "Not enough data"


    # --------------------------------------------------------
    # AI-style recommendation
    # --------------------------------------------------------

    if spending_trend == "Increasing":

        recommendation = (
            "Your spending is increasing. "
            "Consider reviewing your recent expenses "
            "and reducing non-essential spending."
        )

    elif spending_trend == "Decreasing":

        recommendation = (
            "Your spending is decreasing. "
            "Keep maintaining your current spending habits."
        )

    elif spending_trend == "Stable":

        recommendation = (
            "Your spending pattern is relatively stable. "
            "Continue monitoring your expenses."
        )

    else:

        recommendation = (
            "More transaction history is required "
            "to generate a reliable spending trend."
        )


    return jsonify({

        "total_spending":
            total_spending,

        "top_category":
            top_category,

        "top_category_amount":
            top_category_amount,

        "spending_trend":
            spending_trend,

        "recommendation":
            recommendation

    })


# ============================================================
# RECENT TRANSACTIONS API
# ============================================================

@app.route("/transactions")
def transactions():

    df = load_data()

    # Remove accidental spaces from column names
    df.columns = df.columns.str.strip()

    # Check required columns
    required_columns = [
        "date",
        "merchant",
        "amount",
        "type",
        "category"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        return jsonify({
            "error": "Missing columns in dataset",
            "missing_columns": missing_columns,
            "available_columns": df.columns.tolist()
        }), 400

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["date", "amount"]
    )

    df = df.sort_values(
        "date",
        ascending=False
    )

    recent = df.head(10).copy()

    recent["date"] = recent[
        "date"
    ].dt.strftime("%Y-%m-%d")

    recent["amount"] = recent[
        "amount"
    ].astype(float)

    return jsonify({
        "transactions": recent[
            [
                "date",
                "merchant",
                "amount",
                "type",
                "category"
            ]
        ].to_dict(
            orient="records"
        )
    })

# ============================================================
# ERROR HANDLER
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "error": "Endpoint not found",

        "message":
            "The requested API endpoint does not exist."

    }), 404


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )