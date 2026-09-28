import os
import re
import uuid
import json
import hashlib

import pandas as pd
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from sklearn.linear_model import LinearRegression


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_DIR = os.path.join(DATA_DIR, "users")
GOALS_DIR = os.path.join(DATA_DIR, "goals")
AUTH_DIR = os.path.join(DATA_DIR, "auth")

os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(GOALS_DIR, exist_ok=True)
os.makedirs(AUTH_DIR, exist_ok=True)


# ============================================================
# DATA
# ============================================================

COLUMNS = [
    "date",
    "merchant",
    "amount",
    "type",
    "category",
]


# ============================================================
# CATEGORY DETECTION
# ============================================================

CATEGORY_KEYWORDS = {
    "Food": [
        "swiggy", "zomato", "domino", "dominos", "pizza",
        "restaurant", "food", "mcdonald", "kfc", "blinkit",
        "zepto", "instamart"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "meesho",
        "shopping", "mall"
    ],
    "Transport": [
        "uber", "ola", "rapido", "metro", "bus", "train",
        "fuel", "petrol", "diesel"
    ],
    "Entertainment": [
        "netflix", "spotify", "prime video", "hotstar",
        "youtube", "movie", "cinema", "entertainment"
    ],
    "Bills": [
        "electricity", "water", "gas", "recharge", "airtel",
        "jio", "vi", "bill", "internet", "wifi"
    ],
    "Housing": [
        "rent", "housing", "maintenance"
    ],
    "Healthcare": [
        "hospital", "doctor", "pharmacy", "medicine",
        "medical", "healthcare"
    ],
    "Education": [
        "college", "school", "course", "udemy", "coursera",
        "education", "books"
    ],
}


def get_category(merchant):
    merchant = str(merchant or "").lower().strip()

    if merchant == "salary":
        return "Income"

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in merchant for keyword in keywords):
            return category

    return "Other"


# ============================================================
# USER
# ============================================================

def get_user_id():
    user_id = request.headers.get("X-User-ID")

    if not user_id:
        return None

    user_id = str(user_id).strip()

    if len(user_id) > 100:
        return None

    if not re.match(r"^[a-zA-Z0-9_-]+$", user_id):
        return None

    return user_id


def get_user_file():
    user_id = get_user_id()

    if not user_id:
        raise ValueError(
            "User profile not found. Please create a profile."
        )

    return os.path.join(USERS_DIR, f"{user_id}.csv")


def create_user_file(user_id):
    user_id = str(user_id).strip()

    if not re.match(r"^[a-zA-Z0-9_-]+$", user_id):
        raise ValueError("Invalid user ID")

    file_path = os.path.join(USERS_DIR, f"{user_id}.csv")

    if not os.path.exists(file_path):
        pd.DataFrame(columns=COLUMNS).to_csv(
            file_path,
            index=False
        )

    return file_path


# ============================================================
# DATA LOAD / SAVE
# ============================================================

def load_data():
    file_path = get_user_file()

    if not os.path.exists(file_path):
        create_user_file(get_user_id())

    df = pd.read_csv(file_path)

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    for column in COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[COLUMNS].copy()

    if not df.empty:
        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0.0)

        df["type"] = (
            df["type"]
            .astype(str)
            .str.lower()
            .str.strip()
        )

        df["merchant"] = (
            df["merchant"]
            .astype(str)
            .str.strip()
        )

        df["category"] = (
            df["category"]
            .astype(str)
            .str.strip()
        )

        # Repair missing/invalid categories.
        missing = (
            df["category"].isin(["", "nan", "None"])
        )

        if missing.any():
            df.loc[missing, "category"] = (
                df.loc[missing, "merchant"]
                .apply(get_category)
            )

    return df


def save_data(df):
    df = df[COLUMNS].copy()

    df.to_csv(
        get_user_file(),
        index=False
    )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "message": "WealthIQ AI backend is working!",
        "project": "WealthIQ AI",
        "status": "running",
        "model": "Linear Regression",
    })


# ============================================================
# CREATE PROFILE
# ============================================================

@app.route("/create-profile", methods=["POST"])
def create_profile():
    try:
        user_id = str(uuid.uuid4())

        create_user_file(user_id)

        return jsonify({
            "message": "New financial profile created.",
            "user_id": user_id,
        }), 201

    except Exception as e:
        return jsonify({
            "error": "Unable to create profile",
            "message": str(e),
        }), 500


# ============================================================
# AUTHENTICATION
# ============================================================

def auth_file_for_email(email):
    email = str(email or "").strip().lower()
    email_key = hashlib.sha256(email.encode("utf-8")).hexdigest()
    return os.path.join(AUTH_DIR, f"{email_key}.json")


def hash_password(password):
    return hashlib.sha256(str(password).encode("utf-8")).hexdigest()


@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not name or not email or not password:
            return jsonify({
                "success": False,
                "message": "Name, email and password are required."
            }), 400

        if "@" not in email or "." not in email.split("@")[-1]:
            return jsonify({
                "success": False,
                "message": "Please enter a valid email address."
            }), 400

        if len(password) < 6:
            return jsonify({
                "success": False,
                "message": "Password must contain at least 6 characters."
            }), 400

        auth_file = auth_file_for_email(email)
        if os.path.exists(auth_file):
            return jsonify({
                "success": False,
                "message": "An account with this email already exists."
            }), 409

        user_id = str(uuid.uuid4())
        account = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "password_hash": hash_password(password)
        }

        with open(auth_file, "w", encoding="utf-8") as file:
            json.dump(account, file, indent=2)

        create_user_file(user_id)

        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "user_id": user_id,
            "name": name
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required."
            }), 400

        auth_file = auth_file_for_email(email)
        if not os.path.exists(auth_file):
            return jsonify({
                "success": False,
                "message": "No account found with this email."
            }), 401

        with open(auth_file, "r", encoding="utf-8") as file:
            account = json.load(file)

        if account.get("password_hash") != hash_password(password):
            return jsonify({
                "success": False,
                "message": "Incorrect password."
            }), 401

        create_user_file(account["user_id"])

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "user_id": account["user_id"],
            "name": account.get("name", ""),
            "email": account.get("email", email)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# PROFILE CHECK
# ============================================================

@app.route("/profile", methods=["GET"])
def profile():
    try:
        user_id = get_user_id()

        if not user_id:
            return jsonify({
                "profile_exists": False,
                "message": "No user profile found.",
            })

        file_path = os.path.join(
            USERS_DIR,
            f"{user_id}.csv"
        )

        return jsonify({
            "profile_exists": os.path.exists(file_path),
            "user_id": user_id,
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    try:
        df = load_data()

        income = float(
            df.loc[df["type"] == "income", "amount"].sum()
        )

        expenses = float(
            df.loc[df["type"] == "expense", "amount"].sum()
        )

        balance = income - expenses

        expense_df = df[
            df["type"] == "expense"
        ].copy()

        # Monthly spending
        if not expense_df.empty:
            expense_df["date"] = pd.to_datetime(
                expense_df["date"],
                errors="coerce"
            )

            expense_df = expense_df.dropna(
                subset=["date"]
            )

            if not expense_df.empty:
                expense_df["month"] = (
                    expense_df["date"]
                    .dt.to_period("M")
                    .astype(str)
                )

                monthly_values = (
                    expense_df
                    .groupby("month")["amount"]
                    .sum()
                )

                average_monthly_spending = float(
                    monthly_values.mean()
                )
            else:
                average_monthly_spending = 0.0
        else:
            average_monthly_spending = 0.0

        # Budget is based on actual observed spending.
        recommended_budget = (
            average_monthly_spending * 1.10
            if average_monthly_spending > 0
            else 0.0
        )

        if recommended_budget <= 0:
            budget_status = "No spending data"
        elif average_monthly_spending <= recommended_budget:
            budget_status = "Within Budget"
        else:
            budget_status = "Over Budget"

        # Top category
        if not expense_df.empty:
            category_data = (
                expense_df
                .groupby("category")["amount"]
                .sum()
                .sort_values(ascending=False)
            )

            if not category_data.empty:
                top_category = str(category_data.index[0])
                top_category_amount = float(category_data.iloc[0])
            else:
                top_category = "None"
                top_category_amount = 0.0
        else:
            top_category = "None"
            top_category_amount = 0.0

        return jsonify({
            "total_income": income,
            "total_expenses": expenses,
            "balance": balance,

            # This is the observed average monthly spending,
            # not the ML prediction.
            "predicted_spending": average_monthly_spending,

            "recommended_budget": recommended_budget,
            "budget_status": budget_status,

            "top_category": top_category,
            "top_category_amount": top_category_amount,
        })

    except ValueError as e:
        return jsonify({
            "error": "Profile required",
            "message": str(e),
        }), 400

    except Exception as e:
        return jsonify({
            "error": "Unable to load dashboard",
            "message": str(e),
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
        ].copy()

        if expense_df.empty:
            return jsonify({
                "categories": [],
                "amounts": [],
            })

        category_data = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        # Return objects so Chart.js frontend can read
        # category + amount correctly.
        category_list = [
            {
                "category": str(category),
                "amount": float(amount),
            }
            for category, amount in category_data.items()
        ]

        return jsonify({
            "categories": category_list,
            "amounts": [
                float(x)
                for x in category_data.tolist()
            ],
        })

    except Exception as e:
        return jsonify({
            "error": "Unable to load categories",
            "message": str(e),
        }), 500


# ============================================================
# MONTHLY SPENDING
# ============================================================

@app.route("/monthly-spending")
def monthly_spending():
    try:
        df = load_data()

        expense_df = df[
            df["type"] == "expense"
        ].copy()

        if expense_df.empty:
            return jsonify({
                "monthly_spending": [],
                "months": [],
                "amounts": [],
            })

        expense_df["date"] = pd.to_datetime(
            expense_df["date"],
            errors="coerce"
        )

        expense_df = expense_df.dropna(
            subset=["date"]
        )

        if expense_df.empty:
            return jsonify({
                "monthly_spending": [],
                "months": [],
                "amounts": [],
            })

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

        monthly_list = [
            {
                "month": str(month),
                "amount": float(amount),
            }
            for month, amount in monthly.items()
        ]

        return jsonify({
            "monthly_spending": monthly_list,
            "months": [
                str(x)
                for x in monthly.index.tolist()
            ],
            "amounts": [
                float(x)
                for x in monthly.tolist()
            ],
        })

    except Exception as e:
        return jsonify({
            "error": "Unable to load monthly spending",
            "message": str(e),
        }), 500


# ============================================================
# AI SPENDING PREDICTION - LINEAR REGRESSION
# ============================================================

@app.route("/api/predict-spending", methods=["GET"])
def predict_spending():
    try:
        df = load_data()

        expense_df = df[
            df["type"] == "expense"
        ].copy()

        if expense_df.empty:
            return jsonify({
                "success": True,
                "model": "Linear Regression",
                "predictions": [],
                "training_samples": 0,
                "message": (
                    "Add expenses to generate an ML prediction."
                ),
            })

        expense_df["date"] = pd.to_datetime(
            expense_df["date"],
            errors="coerce"
        )

        expense_df = expense_df.dropna(
            subset=["date"]
        )

        if expense_df.empty:
            return jsonify({
                "success": True,
                "model": "Linear Regression",
                "predictions": [],
                "training_samples": 0,
                "message": "Valid expense dates are required.",
            })

        # Aggregate real user expenses by month.
        expense_df["month"] = (
            expense_df["date"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly = (
            expense_df
            .groupby("month")["amount"]
            .sum()
            .reset_index()
            .sort_values("month")
            .reset_index(drop=True)
        )

        monthly["month_index"] = range(
            len(monthly)
        )

        training_samples = len(monthly)

        # --------------------------------------------------------
        # One month of data:
        # Regression cannot learn a slope from one point.
        # We therefore show the actual latest monthly spending
        # and clearly tell the user more data is needed.
        # --------------------------------------------------------

        if training_samples == 1:
            prediction = max(
                0.0,
                float(monthly["amount"].iloc[-1])
            )

            return jsonify({
                "success": True,
                "model": "Linear Regression",
                "predictions": [
                    {
                        "month_ahead": 1,
                        "predicted_spending": round(
                            prediction,
                            2
                        ),
                    }
                ],
                "training_samples": training_samples,
                "monthly_data": [
                    {
                        "month": str(row["month"]),
                        "spending": round(
                            float(row["amount"]),
                            2
                        ),
                    }
                    for _, row in monthly.iterrows()
                ],
                "message": (
                    "Only one month of expense data is available. "
                    "The latest monthly spending is shown until "
                    "more monthly data is added."
                ),
            })

        # --------------------------------------------------------
        # ACTUAL ML MODEL
        # --------------------------------------------------------

        X = monthly[["month_index"]]
        y = monthly["amount"]

        model = LinearRegression()
        model.fit(X, y)

        # Predict next 6 months from the actual user's data.
        future_indices = pd.DataFrame({
            "month_index": range(
                training_samples,
                training_samples + 6
            )
        })

        predictions = model.predict(
            future_indices
        )

        result = []

        for i, prediction in enumerate(
            predictions,
            start=1
        ):
            prediction = max(
                0.0,
                float(prediction)
            )

            result.append({
                "month_ahead": i,
                "predicted_spending": round(
                    prediction,
                    2
                ),
            })

        return jsonify({
            "success": True,
            "model": "Linear Regression",
            "predictions": result,
            "training_samples": training_samples,
            "monthly_data": [
                {
                    "month": str(row["month"]),
                    "spending": round(
                        float(row["amount"]),
                        2
                    ),
                }
                for _, row in monthly.iterrows()
            ],
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "model": "Linear Regression",
            "error": str(e),
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
        ].copy()

        total_spending = float(
            expense_df["amount"].sum()
        )

        if expense_df.empty:
            return jsonify({
                "insights": [
                    "Add expenses to generate personalized insights."
                ],
                "total_spending": 0.0,
                "top_category": "None",
                "top_category_amount": 0.0,
                "spending_trend": "Not enough data",
                "recommendation": (
                    "Add more transactions to generate better insights."
                ),
            })

        category_data = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        top_category = str(
            category_data.index[0]
        )

        top_category_amount = float(
            category_data.iloc[0]
        )

        insights_list = []

        insights_list.append(
            f"Your highest spending category is "
            f"{top_category} with ₹{top_category_amount:,.2f}."
        )

        # Monthly trend
        expense_df["date"] = pd.to_datetime(
            expense_df["date"],
            errors="coerce"
        )

        valid_dates = expense_df.dropna(
            subset=["date"]
        ).copy()

        if not valid_dates.empty:
            valid_dates["month"] = (
                valid_dates["date"]
                .dt.to_period("M")
                .astype(str)
            )

            monthly = (
                valid_dates
                .groupby("month")["amount"]
                .sum()
                .sort_index()
            )

            if len(monthly) >= 2:
                previous = float(monthly.iloc[-2])
                latest = float(monthly.iloc[-1])

                if latest > previous:
                    spending_trend = "Spending is increasing"
                    insights_list.append(
                        "Your latest monthly spending is higher "
                        "than the previous month."
                    )
                    recommendation = (
                        "Consider reducing non-essential spending."
                    )
                elif latest < previous:
                    spending_trend = "Spending is decreasing"
                    insights_list.append(
                        "Your latest monthly spending is lower "
                        "than the previous month."
                    )
                    recommendation = (
                        "Good progress! Continue maintaining "
                        "your spending habits."
                    )
                else:
                    spending_trend = "Spending is stable"
                    insights_list.append(
                        "Your monthly spending is currently stable."
                    )
                    recommendation = (
                        "Your spending is relatively stable."
                    )
            else:
                spending_trend = "Not enough data"
                recommendation = (
                    "Add expenses in another month for a stronger trend."
                )
        else:
            spending_trend = "Not enough data"
            recommendation = (
                "Add valid transaction dates to generate insights."
            )

        return jsonify({
            "insights": insights_list,
            "total_spending": total_spending,
            "top_category": top_category,
            "top_category_amount": top_category_amount,
            "spending_trend": spending_trend,
            "recommendation": recommendation,
        })

    except Exception as e:
        return jsonify({
            "error": "Unable to generate insights",
            "message": str(e),
        }), 500


# ============================================================
# TRANSACTIONS
# ============================================================

@app.route("/transactions")
def transactions():
    try:
        df = load_data()

        recent = df.tail(10).copy()

        records = []

        for _, row in recent.iterrows():
            records.append({
                "date": str(row["date"]),
                "merchant": str(row["merchant"]),
                "amount": float(row["amount"]),
                "type": str(row["type"]),
                "category": str(row["category"]),
            })

        return jsonify({
            "transactions": records
        })

    except Exception as e:
        return jsonify({
            "error": "Unable to load transactions",
            "message": str(e),
        }), 500


# ============================================================
# ADD TRANSACTION
# ============================================================

@app.route("/add-transaction", methods=["POST"])
def add_transaction():
    try:
        data = request.get_json(
            silent=True
        )

        if not data:
            return jsonify({
                "error": "No transaction data received"
            }), 400

        required_fields = [
            "date",
            "merchant",
            "amount",
            "type",
            "category",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in data
            or str(data[field]).strip() == ""
        ]

        # Category may be automatically selected for income.
        if "category" not in data or not str(
            data.get("category", "")
        ).strip():
            if str(data.get("type", "")).lower() == "income":
                data["category"] = "Income"

        missing_fields = [
            field
            for field in required_fields
            if field not in data
            or str(data[field]).strip() == ""
        ]

        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing_fields": missing_fields,
            }), 400

        amount = float(data["amount"])

        if amount <= 0:
            return jsonify({
                "error": "Amount must be greater than zero"
            }), 400

        transaction_type = (
            str(data["type"])
            .lower()
            .strip()
        )

        if transaction_type not in [
            "income",
            "expense",
        ]:
            return jsonify({
                "error": "Type must be income or expense"
            }), 400

        merchant = str(
            data["merchant"]
        ).strip()

        category = str(
            data["category"]
        ).strip()

        # Salary/income always gets Income category.
        if transaction_type == "income":
            category = "Income"

            if not merchant:
                merchant = "Salary"

        # Expense category fallback.
        if transaction_type == "expense":
            if not category or category == "Income":
                category = get_category(
                    merchant
                )

        # Validate date.
        date_value = pd.to_datetime(
            data["date"],
            errors="coerce"
        )

        if pd.isna(date_value):
            return jsonify({
                "error": "Invalid date"
            }), 400

        new_transaction = pd.DataFrame([{
            "date": date_value.strftime("%Y-%m-%d"),
            "merchant": merchant,
            "amount": amount,
            "type": transaction_type,
            "category": category,
        }])

        df = load_data()

        updated_df = pd.concat(
            [
                df,
                new_transaction,
            ],
            ignore_index=True
        )

        save_data(updated_df)

        transaction = (
            new_transaction
            .iloc[0]
            .to_dict()
        )

        transaction["amount"] = float(
            transaction["amount"]
        )

        return jsonify({
            "message": "Transaction added successfully",
            "transaction": transaction,
        }), 201

    except ValueError as e:
        return jsonify({
            "error": "Invalid request",
            "message": str(e),
        }), 400

    except Exception as e:
        return jsonify({
            "error": "Failed to add transaction",
            "message": str(e),
        }), 500



# ============================================================
# SAVINGS GOAL
# ============================================================
def get_goal_file():
    user_id = get_user_id()
    if not user_id:
        raise ValueError("User profile not found. Please create a profile.")
    return os.path.join(GOALS_DIR, f"{user_id}.json")

@app.route("/savings-goal", methods=["GET"])
def get_savings_goal():
    try:
        path = get_goal_file()
        if not os.path.exists(path):
            return jsonify({"goal": None, "message": "No savings goal has been set."})
        with open(path, "r", encoding="utf-8") as file:
            return jsonify({"goal": json.load(file)})
    except ValueError as e:
        return jsonify({"error": "Profile required", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Unable to load savings goal", "message": str(e)}), 500

@app.route("/savings-goal", methods=["POST"])
def save_savings_goal():
    try:
        data = request.get_json(silent=True) or {}
        target = float(data.get("target", 0))
        saved = float(data.get("saved", 0))
        deadline = str(data.get("deadline", "")).strip()
        if target <= 0:
            return jsonify({"error": "Target amount must be greater than zero."}), 400
        if saved < 0 or saved > target:
            return jsonify({"error": "Already saved must be between 0 and the target amount."}), 400
        if deadline:
            deadline_value = pd.to_datetime(deadline, errors="coerce")
            if pd.isna(deadline_value):
                return jsonify({"error": "Invalid target date."}), 400
            deadline = deadline_value.strftime("%Y-%m-%d")
        goal = {"target": round(target,2), "saved": round(saved,2), "deadline": deadline}
        with open(get_goal_file(), "w", encoding="utf-8") as file:
            json.dump(goal, file, indent=2)
        return jsonify({"message": "Savings goal saved successfully.", "goal": goal}), 201
    except ValueError as e:
        return jsonify({"error": "Invalid savings goal", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Unable to save savings goal", "message": str(e)}), 500

@app.route("/savings-goal", methods=["DELETE"])
def delete_savings_goal():
    try:
        path = get_goal_file()
        if os.path.exists(path):
            os.remove(path)
        return jsonify({"message": "Savings goal removed successfully."})
    except ValueError as e:
        return jsonify({"error": "Profile required", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Unable to remove savings goal", "message": str(e)}), 500

# ============================================================
# FINANCIAL HEALTH
# ============================================================

@app.route("/financial-health")
def financial_health():
    try:
        df = load_data()

        income = float(
            df.loc[df["type"] == "income", "amount"].sum()
        )

        expenses = float(
            df.loc[df["type"] == "expense", "amount"].sum()
        )

        if income <= 0:
            return jsonify({
                "score": 0,
                "rating": "Insufficient Data",
                "total_income": 0.0,
                "total_expenses": expenses,
                "savings": -expenses,
                "savings_rate": 0.0,
                "message": (
                    "Add your income to calculate your financial health."
                ),
            })

        savings = income - expenses
        savings_rate = (
            savings / income
        ) * 100

        # Simple explainable financial health score.
        if savings_rate >= 30:
            score = 100
        elif savings_rate >= 20:
            score = 90
        elif savings_rate >= 10:
            score = 75
        elif savings_rate >= 0:
            score = 60
        elif savings_rate >= -10:
            score = 40
        else:
            score = 20

        if score >= 80:
            rating = "Excellent"
        elif score >= 60:
            rating = "Good"
        elif score >= 40:
            rating = "Fair"
        else:
            rating = "Needs Improvement"

        return jsonify({
            "score": score,
            "rating": rating,
            "total_income": income,
            "total_expenses": expenses,
            "savings": savings,
            "savings_rate": round(
                savings_rate,
                2
            ),
            "message": (
                "Financial health calculated successfully."
            ),
        })

    except Exception as e:
        return jsonify({
            "error": "Unable to calculate financial health",
            "message": str(e),
        }), 500


# ============================================================
# RECURRING EXPENSES
# ============================================================

@app.route("/recurring-expenses")
def recurring_expenses():
    """Detect both true recurring expenses and repeated merchant spending.
    Repeated merchants such as Amazon can be detected even when dates and
    amounts are not perfectly regular.
    """
    try:
        df = load_data()
        if df.empty:
            return jsonify({"success": True, "recurring": []})

        expenses = df[df["type"].astype(str).str.lower() == "expense"].copy()
        if expenses.empty:
            return jsonify({"success": True, "recurring": []})

        expenses["date"] = pd.to_datetime(expenses["date"], errors="coerce")
        expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce")
        expenses["merchant_clean"] = (
            expenses["merchant"].astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
        )
        expenses = expenses.dropna(subset=["date", "amount"])

        results = []
        for merchant_key, group in expenses.groupby("merchant_clean"):
            if len(group) < 3:
                continue

            group = group.sort_values("date")
            display_name = str(group["merchant"].iloc[0]).strip() or "Unknown"
            dates = group["date"].drop_duplicates().sort_values()
            amounts = group["amount"].astype(float)
            avg_amount = float(amounts.mean())

            # If dates repeat reasonably often, calculate how regular they are.
            intervals = dates.diff().dt.days.dropna()
            frequency = "Repeated spending"
            monthly_multiplier = 1.0
            regularity = 0.0

            if not intervals.empty:
                avg_interval = float(intervals.mean())
                tolerance = max(3, avg_interval * 0.25)
                regularity = float((abs(intervals - avg_interval) <= tolerance).mean() * 100)

                if 5 <= avg_interval <= 9 and regularity >= 50:
                    frequency = "Likely weekly"
                    monthly_multiplier = 4.33
                elif 20 <= avg_interval <= 40 and regularity >= 50:
                    frequency = "Likely monthly"
                    monthly_multiplier = 30.44 / avg_interval
                elif 75 <= avg_interval <= 110 and regularity >= 50:
                    frequency = "Likely quarterly"
                    monthly_multiplier = 30.44 / avg_interval

            # Amount variation is allowed. This is important for merchants like Amazon.
            if avg_amount > 0:
                amount_variation = float((amounts.max() - amounts.min()) / avg_amount)
            else:
                amount_variation = 0.0

            pattern_type = "recurring" if frequency != "Repeated spending" else "repeated"
            confidence = "High" if len(group) >= 4 and (regularity >= 60 or amount_variation <= 0.40) else "Medium"

            # For irregular repeated purchases, use average amount as a simple
            # monthly-impact indicator rather than falsely claiming a subscription.
            monthly_impact = avg_amount * monthly_multiplier

            results.append({
                "merchant": display_name,
                "frequency": frequency,
                "pattern_type": pattern_type,
                "confidence": confidence,
                "average_amount": round(avg_amount, 2),
                "min_amount": round(float(amounts.min()), 2),
                "max_amount": round(float(amounts.max()), 2),
                "estimated_monthly_impact": round(monthly_impact, 2),
                "occurrences": int(len(group)),
                "regularity": round(regularity, 1),
                "last_date": dates.iloc[-1].strftime("%Y-%m-%d"),
            })

        results.sort(key=lambda x: (x["occurrences"], x["estimated_monthly_impact"]), reverse=True)
        return jsonify({"success": True, "recurring": results[:10]})

    except Exception as e:
        return jsonify({
            "error": "Unable to detect recurring expenses",
            "message": str(e),
        }), 500


# ============================================================
# EXPORT
# ============================================================

@app.route("/export-transactions")
def export_transactions():
    try:
        user_id = get_user_id()

        if not user_id:
            return jsonify({
                "error": "Profile required"
            }), 400

        file_path = get_user_file()

        if not os.path.exists(file_path):
            create_user_file(user_id)

        return send_file(
            file_path,
            mimetype="text/csv",
            as_attachment=True,
            download_name="wealthiq_transactions.csv",
        )

    except Exception as e:
        return jsonify({
            "error": "Failed to export transactions",
            "message": str(e),
        }), 500


# ============================================================
# RESET
# ============================================================

@app.route("/reset-transactions", methods=["POST"])
def reset_transactions():
    try:
        user_id = get_user_id()

        if not user_id:
            return jsonify({
                "error": "Profile required"
            }), 400

        file_path = get_user_file()

        pd.DataFrame(
            columns=COLUMNS
        ).to_csv(
            file_path,
            index=False
        )

        goal_file = os.path.join(GOALS_DIR, f"{user_id}.json")
        if os.path.exists(goal_file):
            os.remove(goal_file)

        return jsonify({
            "message": "Financial profile reset successfully.",
            "total_income": 0,
            "total_expenses": 0,
            "balance": 0,
        })

    except Exception as e:
        return jsonify({
            "error": "Unable to reset financial profile.",
            "message": str(e),
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
