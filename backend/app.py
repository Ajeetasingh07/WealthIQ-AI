import os
import re
import uuid

import pandas as pd

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

CORS(app)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

USERS_DIR = os.path.join(
    DATA_DIR,
    "users"
)

os.makedirs(
    USERS_DIR,
    exist_ok=True
)


# ============================================================
# EMPTY USER DATA
# ============================================================

COLUMNS = [
    "date",
    "merchant",
    "amount",
    "type",
    "category"
]


# ============================================================
# CATEGORY FUNCTION
# ============================================================

def get_category(merchant):

    merchant = str(
        merchant
    ).lower().strip()

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
# USER ID
# ============================================================

def get_user_id():

    user_id = request.headers.get(
        "X-User-ID"
    )

    if not user_id:

        return None

    user_id = str(
        user_id
    ).strip()

    if len(user_id) > 100:
        return None

    if not re.match(
        r"^[a-zA-Z0-9_-]+$",
        user_id
    ):
        return None

    return user_id


# ============================================================
# USER FILE
# ============================================================

def get_user_file():

    user_id = get_user_id()

    if not user_id:

        raise ValueError(
            "User profile not found. Please create a profile."
        )

    return os.path.join(
        USERS_DIR,
        f"{user_id}.csv"
    )


# ============================================================
# CREATE USER DATA
# ============================================================

def create_user_file(user_id):

    if not re.match(
        r"^[a-zA-Z0-9_-]+$",
        user_id
    ):
        raise ValueError(
            "Invalid user ID"
        )

    file_path = os.path.join(
        USERS_DIR,
        f"{user_id}.csv"
    )

    if not os.path.exists(file_path):

        empty_df = pd.DataFrame(
            columns=COLUMNS
        )

        empty_df.to_csv(
            file_path,
            index=False
        )

    return file_path


# ============================================================
# LOAD CURRENT USER DATA
# ============================================================

def load_data():

    file_path = get_user_file()

    if not os.path.exists(file_path):

        create_user_file(
            get_user_id()
        )

    df = pd.read_csv(
        file_path
    )

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    for column in COLUMNS:

        if column not in df.columns:

            df[column] = ""

    df = df[COLUMNS]

    if len(df) > 0:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

        df["type"] = (
            df["type"]
            .astype(str)
            .str.lower()
            .str.strip()
        )

        missing_category = (
            df["category"]
            .astype(str)
            .str.strip()
            .isin([
                "",
                "nan",
                "None"
            ])
        )

        if missing_category.any():

            df.loc[
                missing_category,
                "category"
            ] = df.loc[
                missing_category,
                "merchant"
            ].apply(
                get_category
            )

    return df


# ============================================================
# SAVE CURRENT USER DATA
# ============================================================

def save_data(df):

    file_path = get_user_file()

    df.to_csv(
        file_path,
        index=False
    )


# ============================================================
# HOME
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
# CREATE PROFILE
# ============================================================

@app.route(
    "/create-profile",
    methods=["POST"]
)
def create_profile():

    try:

        new_user_id = str(
            uuid.uuid4()
        )

        create_user_file(
            new_user_id
        )

        return jsonify({

            "message":
                "New financial profile created.",

            "user_id":
                new_user_id

        }), 201

    except Exception as e:

        return jsonify({

            "error":
                "Unable to create profile",

            "message":
                str(e)

        }), 500


# ============================================================
# PROFILE CHECK
# ============================================================

@app.route(
    "/profile",
    methods=["GET"]
)
def profile():

    try:

        user_id = get_user_id()

        if not user_id:

            return jsonify({

                "profile_exists":
                    False,

                "message":
                    "No user profile found."

            })

        file_path = os.path.join(
            USERS_DIR,
            f"{user_id}.csv"
        )

        exists = os.path.exists(
            file_path
        )

        return jsonify({

            "profile_exists":
                exists,

            "user_id":
                user_id

        })

    except Exception as e:

        return jsonify({

            "error":
                str(e)

        }), 500


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    try:

        df = load_data()

        income = df[
            df["type"] == "income"
        ]["amount"].sum()

        expenses = df[
            df["type"] == "expense"
        ]["amount"].sum()

        balance = (
            income -
            expenses
        )

        expense_df = df[
            df["type"] == "expense"
        ]

        if len(expense_df) > 0:

            predicted_spending = (
                expense_df["amount"].mean()
                *
                min(
                    len(expense_df),
                    30
                )
            )

        else:

            predicted_spending = 0


        recommended_budget = (
            predicted_spending *
            1.10
        )


        if expenses <= recommended_budget:

            budget_status = (
                "Within Budget"
            )

        else:

            budget_status = (
                "Over Budget"
            )


        category_df = (
            expense_df
            .groupby("category")[
                "amount"
            ]
            .sum()
        )


        if len(category_df) > 0:

            top_category = (
                category_df.idxmax()
            )

            top_category_amount = (
                category_df.max()
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
                float(
                    predicted_spending
                ),

            "recommended_budget":
                float(
                    recommended_budget
                ),

            "budget_status":
                budget_status,

            "top_category":
                str(
                    top_category
                ),

            "top_category_amount":
                float(
                    top_category_amount
                )

        })


    except ValueError as e:

        return jsonify({

            "error":
                "Profile required",

            "message":
                str(e)

        }), 400


    except Exception as e:

        return jsonify({

            "error":
                "Unable to load dashboard",

            "message":
                str(e)

        }), 500


# ============================================================
# CATEGORIES
# ============================================================

@app.route("/categories")
def categories():

    try:

        df = load_data()

        expense_df = df[
            df["type"] == "expense"
        ]

        category_data = (
            expense_df
            .groupby("category")[
                "amount"
            ]
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
# MONTHLY SPENDING
# ============================================================

@app.route("/monthly-spending")
def monthly_spending():

    try:

        df = load_data()

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        expense_df = df[
            df["type"] == "expense"
        ].copy()

        expense_df["month"] = (
            expense_df["date"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly = (
            expense_df
            .groupby("month")[
                "amount"
            ]
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
# INSIGHTS
# ============================================================

@app.route("/insights")
def insights():

    try:

        df = load_data()

        expense_df = df[
            df["type"] == "expense"
        ]

        total_spending = (
            expense_df["amount"].sum()
        )

        category_data = (
            expense_df
            .groupby("category")[
                "amount"
            ]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if len(category_data) > 0:

            top_category = (
                category_data.index[0]
            )

            top_category_amount = (
                category_data.iloc[0]
            )

        else:

            top_category = "None"

            top_category_amount = 0


        if len(expense_df) >= 2:

            first_half = (
                expense_df[
                    "amount"
                ]
                .iloc[
                    :len(expense_df)//2
                ]
                .sum()
            )

            second_half = (
                expense_df[
                    "amount"
                ]
                .iloc[
                    len(expense_df)//2:
                ]
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
                float(
                    total_spending
                ),

            "top_category":
                str(
                    top_category
                ),

            "top_category_amount":
                float(
                    top_category_amount
                ),

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
# TRANSACTIONS
# ============================================================

@app.route("/transactions")
def transactions():

    try:

        df = load_data()

        recent = (
            df.tail(10)
            .copy()
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
# ADD TRANSACTION
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

            or str(
                data[field]
            ).strip() == ""

        ]


        if missing_fields:

            return jsonify({

                "error":
                    "Missing required fields",

                "missing_fields":
                    missing_fields

            }), 400


        amount = float(
            data["amount"]
        )


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


        df = load_data()


        new_transaction = pd.DataFrame([{

            "date":
                str(
                    data["date"]
                ),

            "merchant":
                str(
                    data["merchant"]
                ).strip(),

            "amount":
                amount,

            "type":
                transaction_type,

            "category":
                str(
                    data["category"]
                ).strip()

        }])


        updated_df = pd.concat(

            [
                df,
                new_transaction
            ],

            ignore_index=True

        )


        save_data(
            updated_df
        )


        return jsonify({

            "message":
                "Transaction added successfully",

            "transaction":
                new_transaction
                .iloc[0]
                .to_dict()

        }), 201


    except ValueError as e:

        return jsonify({

            "error":
                "Invalid request",

            "message":
                str(e)

        }), 400


    except Exception as e:

        return jsonify({

            "error":
                "Failed to add transaction",

            "message":
                str(e)

        }), 500


# ============================================================
# FINANCIAL HEALTH
# ============================================================

@app.route("/financial-health")
def financial_health():

    try:

        df = load_data()

        income = df[
            df["type"] == "income"
        ]["amount"].sum()

        expenses = df[
            df["type"] == "expense"
        ]["amount"].sum()


        if income <= 0:

            return jsonify({

                "score":
                    0,

                "rating":
                    "Insufficient Data",

                "total_income":
                    0,

                "total_expenses":
                    float(expenses),

                "savings":
                    -float(expenses),

                "savings_rate":
                    0,

                "message":
                    "Add your income transactions to calculate your financial health."

            })


        savings = (
            income -
            expenses
        )


        savings_rate = (
            savings /
            income
        ) * 100


        score = 100


        if savings_rate < 0:

            score -= 50

        elif savings_rate < 10:

            score -= 30

        elif savings_rate < 20:

            score -= 15


        score = max(
            0,
            min(
                100,
                score
            )
        )


        if score >= 80:

            rating = "Excellent"

        elif score >= 60:

            rating = "Good"

        elif score >= 40:

            rating = "Fair"

        else:

            rating = (
                "Needs Improvement"
            )


        return jsonify({

            "score":
                int(score),

            "rating":
                rating,

            "total_income":
                float(income),

            "total_expenses":
                float(expenses),

            "savings":
                float(savings),

            "savings_rate":
                round(
                    float(
                        savings_rate
                    ),
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


# ============================================================
# EXPORT CURRENT USER
# ============================================================

@app.route(
    "/export-transactions"
)
def export_transactions():

    try:

        file_path = get_user_file()

        if not os.path.exists(
            file_path
        ):

            create_user_file(
                get_user_id()
            )


        return send_file(

            file_path,

            mimetype="text/csv",

            as_attachment=True,

            download_name=
                "wealthiq_transactions.csv"

        )


    except Exception as e:

        return jsonify({

            "error":
                "Failed to export transactions",

            "message":
                str(e)

        }), 500


# ============================================================
# RESET CURRENT USER
# ============================================================

@app.route(
    "/reset-transactions",
    methods=["POST"]
)
def reset_transactions():

    try:

        user_id = get_user_id()

        file_path = get_user_file()


        empty_df = pd.DataFrame(
            columns=COLUMNS
        )


        empty_df.to_csv(
            file_path,
            index=False
        )


        return jsonify({

            "message":
                "Financial profile reset successfully.",

            "total_income":
                0,

            "total_expenses":
                0,

            "balance":
                0

        })


    except Exception as e:

        return jsonify({

            "error":
                "Unable to reset financial profile.",

            "message":
                str(e)

        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )