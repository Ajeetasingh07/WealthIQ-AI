import os
import pandas as pd

from flask import Flask, jsonify, request
from flask_cors import CORS


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

CORS(app)


# ============================================================
# FILE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "transactions.csv"
)


# ============================================================
# CATEGORY FUNCTION
# ============================================================

def get_category(merchant):

    merchant = str(merchant).lower().strip()

    if merchant in [
        "swiggy",
        "zomato",
        "dominos"
    ]:
        return "Food"

    elif merchant in [
        "amazon",
        "flipkart",
        "myntra"
    ]:
        return "Shopping"

    elif merchant in [
        "uber",
        "ola"
    ]:
        return "Transport"

    elif merchant in [
        "netflix",
        "spotify"
    ]:
        return "Entertainment"

    elif merchant in [
        "electricity",
        "water",
        "gas"
    ]:
        return "Bills"

    elif merchant in [
        "rent",
        "housing"
    ]:
        return "Housing"

    elif merchant == "salary":

        return "Income"

    else:

        return "Other"


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

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    # Make sure category exists

    if "category" not in df.columns:

        df["category"] = df[
            "merchant"
        ].apply(get_category)

    return df


# ============================================================
# HOME API
# ============================================================

@app.route("/")
def home():

    return jsonify({

        "message":
            "WealthIQ AI backend is working!",

        "project":
            "WealthIQ AI",

        "status":
            "running"

    })


# ============================================================
# DASHBOARD API
# ============================================================

@app.route("/dashboard")
def dashboard():

    try:

        df = load_data()

        # Convert amount to numeric

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        # Income

        income = df[
            df["type"].str.lower() == "income"
        ]["amount"].sum()

        # Expenses

        expenses = df[
            df["type"].str.lower() == "expense"
        ]["amount"].sum()

        # Balance

        balance = income - expenses

        # Simple predicted spending

        expense_df = df[
            df["type"].str.lower() == "expense"
        ]

        if len(expense_df) > 0:

            predicted_spending = (
                expense_df["amount"]
                .mean() *
                min(len(expense_df), 30)
            )

        else:

            predicted_spending = 0

        # Recommended budget

        recommended_budget = (
            predicted_spending * 1.10
        )

        if expenses <= recommended_budget:

            budget_status = "Within Budget"

        else:

            budget_status = "Over Budget"

        # Top category

        category_df = expense_df.groupby(
            "category"
        )["amount"].sum()

        if len(category_df) > 0:

            top_category = (
                category_df
                .idxmax()
            )

            top_category_amount = (
                category_df
                .max()
            )

        else:

            top_category = "None"

            top_category_amount = 0

        return jsonify({

            "total_income":
                float(income),

            "total_expenses":
                float(expenses),

            "balance":
                float(balance),

            "predicted_spending":
                float(predicted_spending),

            "recommended_budget":
                float(recommended_budget),

            "budget_status":
                budget_status,

            "top_category":
                str(top_category),

            "top_category_amount":
                float(top_category_amount)

        })

    except Exception as e:

        return jsonify({

            "error":
                "Unable to load dashboard",

            "message":
                str(e)

        }), 500


# ============================================================
# CATEGORY API
# ============================================================

@app.route("/categories")
def categories():

    try:

        df = load_data()

        expense_df = df[
            df["type"].str.lower() == "expense"
        ]

        category_data = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        return jsonify({

            "categories":
                category_data
                .index
                .astype(str)
                .tolist(),

            "amounts":
                category_data
                .astype(float)
                .tolist()

        })

    except Exception as e:

        return jsonify({

            "error":
                "Unable to load categories",

            "message":
                str(e)

        }), 500


# ============================================================
# MONTHLY SPENDING API
# ============================================================

@app.route("/monthly-spending")
def monthly_spending():

    try:

        df = load_data()

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        expense_df = df[
            df["type"].str.lower() == "expense"
        ].copy()

        expense_df["month"] = (
            expense_df["date"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly = (
            expense_df
            .groupby("month")["amount"]
            .sum()
            .sort_index()
        )

        return jsonify({

            "months":
                monthly
                .index
                .astype(str)
                .tolist(),

            "amounts":
                monthly
                .astype(float)
                .tolist()

        })

    except Exception as e:

        return jsonify({

            "error":
                "Unable to load monthly spending",

            "message":
                str(e)

        }), 500


# ============================================================
# INSIGHTS API
# ============================================================

@app.route("/insights")
def insights():

    try:

        df = load_data()

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        expense_df = df[
            df["type"].str.lower() == "expense"
        ]

        total_spending = (
            expense_df["amount"].sum()
        )

        category_data = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if len(category_data) > 0:

            top_category = (
                category_data
                .index[0]
            )

            top_category_amount = (
                category_data
                .iloc[0]
            )

        else:

            top_category = "None"

            top_category_amount = 0

        # Simple spending trend

        if len(expense_df) >= 2:

            first_half = (
                expense_df["amount"]
                .iloc[:len(expense_df)//2]
                .sum()
            )

            second_half = (
                expense_df["amount"]
                .iloc[len(expense_df)//2:]
                .sum()
            )

            if second_half > first_half:

                spending_trend = (
                    "Spending is increasing"
                )

                recommendation = (
                    "Consider reducing "
                    "non-essential spending."
                )

            elif second_half < first_half:

                spending_trend = (
                    "Spending is decreasing"
                )

                recommendation = (
                    "Good progress! "
                    "Continue maintaining "
                    "your spending habits."
                )

            else:

                spending_trend = (
                    "Spending is stable"
                )

                recommendation = (
                    "Your spending is "
                    "relatively stable."
                )

        else:

            spending_trend = (
                "Not enough data"
            )

            recommendation = (
                "Add more transactions "
                "to generate better insights."
            )

        return jsonify({

            "total_spending":
                float(total_spending),

            "top_category":
                str(top_category),

            "top_category_amount":
                float(top_category_amount),

            "spending_trend":
                spending_trend,

            "recommendation":
                recommendation

        })

    except Exception as e:

        return jsonify({

            "error":
                "Unable to generate insights",

            "message":
                str(e)

        }), 500


# ============================================================
# RECENT TRANSACTIONS API
# ============================================================

@app.route("/transactions")
def transactions():

    try:

        df = load_data()

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

                "error":
                    "Missing columns in dataset",

                "missing_columns":
                    missing_columns,

                "available_columns":
                    df.columns.tolist()

            }), 400

        recent = df.tail(10).copy()

        recent["amount"] = pd.to_numeric(
            recent["amount"],
            errors="coerce"
        )

        recent["date"] = (
            recent["date"]
            .astype(str)
        )

        records = []

        for _, row in recent.iterrows():

            records.append({

                "date":
                    str(row["date"]),

                "merchant":
                    str(row["merchant"]),

                "amount":
                    float(row["amount"]),

                "type":
                    str(row["type"]),

                "category":
                    str(row["category"])

            })

        return jsonify({

            "transactions":
                records

        })

    except Exception as e:

        return jsonify({

            "error":
                "Unable to load transactions",

            "message":
                str(e)

        }), 500


# ============================================================
# ADD NEW TRANSACTION API
# ============================================================

@app.route(
    "/add-transaction",
    methods=["POST"]
)
def add_transaction():

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "error":
                    "No transaction data received"

            }), 400

        required_fields = [
            "date",
            "merchant",
            "amount",
            "type",
            "category"
        ]

        missing_fields = [

            field

            for field in required_fields

            if field not in data
            or str(data[field]).strip() == ""

        ]

        if missing_fields:

            return jsonify({

                "error":
                    "Missing required fields",

                "missing_fields":
                    missing_fields

            }), 400

        # Validate amount

        try:

            amount = float(
                data["amount"]
            )

        except (
            ValueError,
            TypeError
        ):

            return jsonify({

                "error":
                    "Amount must be a number"

            }), 400

        # Validate type

        transaction_type = str(
            data["type"]
        ).lower().strip()

        if transaction_type not in [
            "income",
            "expense"
        ]:

            return jsonify({

                "error":
                    "Type must be income or expense"

            }), 400

        # Load current CSV

        current_df = pd.read_csv(
            DATA_FILE
        )

        current_df.columns = (
            current_df
            .columns
            .str.strip()
            .str.lower()
        )

        # Create category for old data
        # if category does not exist

        if "category" not in current_df.columns:

            current_df["category"] = (
                current_df["merchant"]
                .apply(get_category)
            )

        # New transaction

        new_transaction = pd.DataFrame([{

            "date":
                str(data["date"]),

            "merchant":
                str(data["merchant"])
                .strip(),

            "amount":
                amount,

            "type":
                transaction_type,

            "category":
                str(data["category"])
                .strip()

        }])

        # Add transaction

        updated_df = pd.concat(

            [
                current_df,
                new_transaction
            ],

            ignore_index=True

        )

        # Save CSV

        updated_df.to_csv(

            DATA_FILE,

            index=False

        )

        return jsonify({

            "message":
                "Transaction added successfully",

            "transaction": {

                "date":
                    str(data["date"]),

                "merchant":
                    str(data["merchant"]),

                "amount":
                    amount,

                "type":
                    transaction_type,

                "category":
                    str(data["category"])

            }

        }), 201

    except Exception as e:

        return jsonify({

            "error":
                "Failed to add transaction",

            "message":
                str(e)

        }), 500


# ============================================================
# START SERVER
# ============================================================
# ============================================================
# FINANCIAL HEALTH SCORE API
# ============================================================

@app.route("/financial-health")
def financial_health():

    try:

        df = load_data()

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        income = df[
            df["type"].str.lower() == "income"
        ]["amount"].sum()

        expenses = df[
            df["type"].str.lower() == "expense"
        ]["amount"].sum()

        if income <= 0:

            return jsonify({
                "score": 0,
                "rating": "Insufficient Data",
                "message": "Add income transactions to calculate your financial health."
            })

        savings = income - expenses

        savings_rate = (
            savings / income
        ) * 100

        # Start with 100 points
        score = 100

        # Penalize overspending
        if savings_rate < 0:
            score -= 50

        elif savings_rate < 10:
            score -= 30

        elif savings_rate < 20:
            score -= 15

        # Keep score between 0 and 100
        score = max(
            0,
            min(100, score)
        )

        if score >= 80:
            rating = "Excellent"
        elif score >= 60:
            rating = "Good"
        elif score >= 40:
            rating = "Fair"
        else:
            rating = "Needs Improvement"

        return jsonify({

            "score": int(score),

            "rating": rating,

            "total_income":
                float(income),

            "total_expenses":
                float(expenses),

            "savings":
                float(savings),

            "savings_rate":
                round(
                    float(savings_rate),
                    2
                ),

            "message":
                "Financial health calculated successfully."

        })

    except Exception as e:

        return jsonify({

            "error":
                "Unable to calculate financial health",

            "message":
                str(e)

        }), 500
if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )