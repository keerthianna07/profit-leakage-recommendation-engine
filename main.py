import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ============================================
# 1. LOAD DATA
# ============================================

file_path = "Data/ECOMM DATA.xlsx"

df = pd.read_excel(file_path)

print("Dataset loaded successfully!")
print("Original shape:", df.shape)


# ============================================
# 2. BASIC CLEANING
# ============================================

if "Postal Code" in df.columns:
    df = df.drop(columns=["Postal Code"])

df["Order Date"] = pd.to_datetime(df["Order Date"])
df["Ship Date"] = pd.to_datetime(df["Ship Date"])


# ============================================
# 3. FEATURE ENGINEERING
# ============================================

sales_safe = df["Sales"].replace(0, np.nan)

df["Profit Margin"] = df["Profit"] / sales_safe

df["Shipping Ratio"] = df["Shipping Cost"] / sales_safe

df["Discount Impact"] = df["Discount"] * df["Sales"]

df["Delivery Time"] = (
    df["Ship Date"] - df["Order Date"]
).dt.days

df["Profit Margin"] = df["Profit Margin"].fillna(0)
df["Shipping Ratio"] = df["Shipping Ratio"].fillna(0)
df["Discount Impact"] = df["Discount Impact"].fillna(0)
df["Delivery Time"] = df["Delivery Time"].fillna(0)


# ============================================
# 4. SELECT MODEL FEATURES
# ============================================

numeric_features = [
    "Sales",
    "Quantity",
    "Discount",
    "Shipping Cost",
    "Profit",
    "Profit Margin",
    "Shipping Ratio",
    "Discount Impact",
    "Delivery Time"
]

categorical_features = [
    "Ship Mode",
    "Segment",
    "Market",
    "Region",
    "Category",
    "Sub-Category",
    "Order Priority"
]


# Keep only the features we actually want
model_data = df[numeric_features + categorical_features].copy()


# Convert categorical variables to dummy variables
model_data = pd.get_dummies(
    model_data,
    columns=categorical_features,
    drop_first=True,
    dtype=float
)


# Handle missing values
model_data = model_data.fillna(0)


# Final feature matrix
X = model_data


print("\nModel feature count:", X.shape[1])
print("Model data shape:", X.shape)

print("\nSelected numerical features:")
print(numeric_features)

print("\nSelected categorical features:")
print(categorical_features)


# ============================================
# 5. TRAIN / TEST SPLIT
# ============================================

train_indices, test_indices = train_test_split(
    X.index,
    test_size=0.20,
    random_state=42
)

X_train = X.loc[train_indices]
X_test = X.loc[test_indices]

print("Training rows:", X_train.shape[0])
print("Testing rows:", X_test.shape[0])


# ============================================
# 6. SCALE DATA
# ============================================

scaler = StandardScaler()

# IMPORTANT:
# Fit ONLY on training data
X_train_scaled = scaler.fit_transform(X_train)

# Apply the same transformation to test data
X_test_scaled = scaler.transform(X_test)

# Convert to float32 for TensorFlow
X_train_scaled = X_train_scaled.astype("float32")
X_test_scaled = X_test_scaled.astype("float32")


print("\nScaling completed!")
print("Training matrix:", X_train_scaled.shape)
print("Testing matrix:", X_test_scaled.shape)

# ============================================
# 7. BUILD DEEP AUTOENCODER
# ============================================

input_dim = X_train_scaled.shape[1]

autoencoder = Sequential([
    Dense(32, activation="relu", input_shape=(input_dim,)),
    Dense(16, activation="relu"),
    Dense(8, activation="relu"),
    Dense(16, activation="relu"),
    Dense(32, activation="relu"),
    Dense(input_dim, activation="linear")
])

autoencoder.compile(
    optimizer="adam",
    loss="mse"
)

print("\nDeep Autoencoder:")
autoencoder.summary()

# ============================================
# 8. TRAIN AUTOENCODER
# ============================================

history = autoencoder.fit(
    X_train_scaled,
    X_train_scaled,
    epochs=20,
    batch_size=256,
    validation_data=(X_test_scaled, X_test_scaled),
    shuffle=True,
    verbose=1
)

print("\nTraining completed!")

# ============================================
# 9. RECONSTRUCTION ERROR
# ============================================

# Reconstruct the test transactions
X_test_reconstructed = autoencoder.predict(
    X_test_scaled,
    verbose=0
)

# Calculate Mean Squared Error for each transaction
reconstruction_error = np.mean(
    np.square(X_test_scaled - X_test_reconstructed),
    axis=1
)

print("\nReconstruction error calculated!")

print("Minimum error:", reconstruction_error.min())
print("Maximum error:", reconstruction_error.max())
print("Mean error:", reconstruction_error.mean())
print("Median error:", np.median(reconstruction_error))

# ============================================
# 10. ANOMALY THRESHOLD
# ============================================

threshold_95 = np.percentile(
    reconstruction_error,
    95
)

anomaly_flags = (
    reconstruction_error > threshold_95
)

print("\n95th percentile threshold:", threshold_95)

print(
    "Anomalies detected:",
    anomaly_flags.sum(),
    "/",
    len(anomaly_flags)
)

print(
    "Anomaly percentage:",
    anomaly_flags.mean() * 100,
    "%"
)

# ============================================
# 11. BUILD ANOMALY RESULTS
# ============================================

# Get the original test transactions
test_results = df.loc[test_indices].copy()

# Add reconstruction error
test_results["Reconstruction Error"] = reconstruction_error

# Add anomaly prediction
test_results["Anomaly"] = anomaly_flags.astype(int)

# Business proxy:
# Negative profit = potential profit leakage
test_results["Actual Leakage Proxy"] = (
    test_results["Profit"] < 0
).astype(int)


print("\n============================================")
print("ANOMALY EVALUATION")
print("============================================")

print(
    "\nPotential anomalies detected:",
    test_results["Anomaly"].sum()
)

print(
    "Negative-profit transactions:",
    test_results["Actual Leakage Proxy"].sum()
)

print(
    "Negative-profit transactions among anomalies:",
    test_results.loc[
        test_results["Anomaly"] == 1,
        "Actual Leakage Proxy"
    ].sum()
)

# ============================================
# 12. CONFUSION MATRIX
# ============================================

from sklearn.metrics import (
    confusion_matrix,
    classification_report
)

cm = confusion_matrix(
    test_results["Actual Leakage Proxy"],
    test_results["Anomaly"]
)

print("\nConfusion Matrix:")
print(cm)

print("\nClassification Report:")
print(
    classification_report(
        test_results["Actual Leakage Proxy"],
        test_results["Anomaly"],
        target_names=["Non-negative Profit", "Negative Profit"]
    )
)

# ============================================
# 13. THRESHOLD COMPARISON
# ============================================

from sklearn.metrics import precision_score, recall_score, f1_score

percentiles = [90, 92.5, 95, 97.5, 99]

print("\n============================================")
print("THRESHOLD COMPARISON")
print("============================================")

print(
    f"{'Threshold':<12}"
    f"{'Anomalies':<12}"
    f"{'Precision':<12}"
    f"{'Recall':<12}"
    f"{'F1':<12}"
)

for percentile in percentiles:

    threshold = np.percentile(
        reconstruction_error,
        percentile
    )

    predictions = (
        reconstruction_error > threshold
    ).astype(int)

    precision = precision_score(
        test_results["Actual Leakage Proxy"],
        predictions,
        zero_division=0
    )

    recall = recall_score(
        test_results["Actual Leakage Proxy"],
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        test_results["Actual Leakage Proxy"],
        predictions,
        zero_division=0
    )

    print(
        f"{percentile:<12}"
        f"{predictions.sum():<12}"
        f"{precision:<12.3f}"
        f"{recall:<12.3f}"
        f"{f1:<12.3f}"
    )

    # ============================================
    # 14. BUSINESS IMPACT BY THRESHOLD
    # ============================================

    print("\n============================================")
    print("BUSINESS IMPACT BY THRESHOLD")
    print("============================================")

    print(
        f"{'Threshold':<12}"
        f"{'Anomalies':<12}"
        f"{'Neg-Profit':<12}"
        f"{'Customers':<12}"
        f"{'Sales':<15}"
        f"{'Profit':<15}"
        f"{'Loss':<15}"
    )

    for percentile in percentiles:
        threshold = np.percentile(
            reconstruction_error,
            percentile
        )

        predictions = (
                reconstruction_error > threshold
        )

        # Get transactions flagged at this threshold
        flagged = test_results.loc[predictions].copy()

        # Number of negative-profit transactions
        negative_profit_count = (
                flagged["Profit"] < 0
        ).sum()

        # Number of unique customers affected
        customer_count = flagged["Customer ID"].nunique()

        # Total sales associated with flagged transactions
        total_sales = flagged["Sales"].sum()

        # Total profit associated with flagged transactions
        total_profit = flagged["Profit"].sum()

        # Actual negative-profit amount
        total_loss = flagged.loc[
            flagged["Profit"] < 0,
            "Profit"
        ].sum()

        print(
            f"{percentile:<12}"
            f"{len(flagged):<12}"
            f"{negative_profit_count:<12}"
            f"{customer_count:<12}"
            f"{total_sales:<15.2f}"
            f"{total_profit:<15.2f}"
            f"{total_loss:<15.2f}"
        )

# ============================================
# 15. CUSTOMER PROFIT-LEAKAGE PROFILE
# ============================================

# Use the tentative 95% threshold
customer_threshold = np.percentile(
    reconstruction_error,
    95
)

# Identify the 95% anomalous transactions
customer_anomalies = (
    reconstruction_error > customer_threshold
)

# Create a copy of the test transactions
customer_data = test_results.copy()

# Store anomaly status
customer_data["Anomaly"] = (
    customer_anomalies.astype(int)
)


# ============================================
# CUSTOMER-LEVEL AGGREGATION
# ============================================

customer_profiles = (
    customer_data
    .groupby("Customer ID")
    .agg(
        Total_Orders=("Order ID", "nunique"),
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Profit", "sum"),

        Negative_Profit_Orders=(
            "Profit",
            lambda x: (x < 0).sum()
        ),

        Anomalous_Orders=(
            "Anomaly",
            "sum"
        ),

        Average_Discount=(
            "Discount",
            "mean"
        ),

        Average_Profit_Margin=(
            "Profit Margin",
            "mean"
        ),

        Average_Shipping_Ratio=(
            "Shipping Ratio",
            "mean"
        ),

        Total_Discount_Impact=(
            "Discount Impact",
            "sum"
        )
    )
    .reset_index()
)


# ============================================
# CUSTOMER ANOMALY RATE
# ============================================

customer_profiles["Anomaly_Rate"] = (
    customer_profiles["Anomalous_Orders"]
    / customer_profiles["Total_Orders"]
)


# ============================================
# POTENTIAL LOSS
# ============================================

customer_profiles["Potential_Loss"] = (
    customer_data
    .assign(
        Negative_Loss=lambda x: x["Profit"].where(
            x["Profit"] < 0,
            0
        )
    )
    .groupby("Customer ID")["Negative_Loss"]
    .sum()
    .abs()
    .reindex(customer_profiles["Customer ID"])
    .fillna(0)
    .values
)


# ============================================
# SORT CUSTOMERS BY POTENTIAL LOSS
# ============================================

customer_profiles = customer_profiles.sort_values(
    by="Potential_Loss",
    ascending=False
)


print("\n============================================")
print("CUSTOMER PROFIT-LEAKAGE PROFILE")
print("============================================")

print(
    "\nTotal customers analyzed:",
    len(customer_profiles)
)

print(
    "Customers with anomalous transactions:",
    (
        customer_profiles["Anomalous_Orders"] > 0
    ).sum()
)

print("\nTop 10 customers by potential loss:")

print(
    customer_profiles[
        [
            "Customer ID",
            "Total_Orders",
            "Total_Sales",
            "Total_Profit",
            "Negative_Profit_Orders",
            "Anomalous_Orders",
            "Anomaly_Rate",
            "Average_Discount",
            "Average_Profit_Margin",
            "Average_Shipping_Ratio",
            "Potential_Loss"
        ]
    ].head(10)
)

# ============================================
# 16. CUSTOMER RISK SCORE
# ============================================

# Make copies so the original values remain available
risk_data = customer_profiles.copy()


# --------------------------------------------
# 1. ANOMALY RISK
# --------------------------------------------

# Convert anomaly rate to a 0-100 percentile score
risk_data["Anomaly_Risk"] = (
    risk_data["Anomaly_Rate"]
    .rank(pct=True)
    * 100
)


# --------------------------------------------
# 2. LOSS RISK
# --------------------------------------------

risk_data["Loss_Risk"] = (
    risk_data["Potential_Loss"]
    .rank(pct=True)
    * 100
)


# --------------------------------------------
# 3. DISCOUNT RISK
# --------------------------------------------

risk_data["Discount_Risk"] = (
    risk_data["Average_Discount"]
    .rank(pct=True)
    * 100
)


# --------------------------------------------
# 4. SHIPPING RISK
# --------------------------------------------

risk_data["Shipping_Risk"] = (
    risk_data["Average_Shipping_Ratio"]
    .rank(pct=True)
    * 100
)


# --------------------------------------------
# 5. COMBINED RISK SCORE
# --------------------------------------------

risk_data["Risk_Score"] = (
    0.35 * risk_data["Anomaly_Risk"]
    + 0.35 * risk_data["Loss_Risk"]
    + 0.15 * risk_data["Discount_Risk"]
    + 0.15 * risk_data["Shipping_Risk"]
)


# --------------------------------------------
# 6. RISK CATEGORY
# --------------------------------------------

def classify_risk(score):

    if score >= 75:
        return "CRITICAL"

    elif score >= 50:
        return "HIGH"

    elif score >= 25:
        return "MEDIUM"

    else:
        return "LOW"


risk_data["Risk_Category"] = (
    risk_data["Risk_Score"]
    .apply(classify_risk)
)


# --------------------------------------------
# 7. DISPLAY TOP CUSTOMERS
# --------------------------------------------

risk_data = risk_data.sort_values(
    by="Risk_Score",
    ascending=False
)


print("\n============================================")
print("CUSTOMER RISK ANALYSIS")
print("============================================")

print(
    "\nRisk category distribution:"
)

print(
    risk_data["Risk_Category"]
    .value_counts()
)


print("\nTop 15 high-risk customers:")

print(
    risk_data[
        [
            "Customer ID",
            "Risk_Score",
            "Risk_Category",
            "Anomaly_Rate",
            "Potential_Loss",
            "Average_Discount",
            "Average_Profit_Margin",
            "Average_Shipping_Ratio"
        ]
    ].head(15)
)

# ============================================
# 17. PRIORITY CUSTOMER IDENTIFICATION
# ============================================

# Customers with at least one anomalous transaction
priority_customers = risk_data[
    (risk_data["Anomalous_Orders"] > 0)
].copy()

# Customers with both anomaly evidence AND
# negative-profit exposure
high_priority_customers = risk_data[
    (risk_data["Anomalous_Orders"] > 0)
    &
    (risk_data["Potential_Loss"] > 0)
].copy()


print("\n============================================")
print("PRIORITY CUSTOMER ANALYSIS")
print("============================================")

print(
    "Customers with anomalies:",
    len(priority_customers)
)

print(
    "Customers with anomalies + potential loss:",
    len(high_priority_customers)
)

print("\nRisk distribution among priority customers:")

print(
    priority_customers["Risk_Category"]
    .value_counts()
)

# ============================================
# 18. LEAKAGE PATTERN CLASSIFICATION
# ============================================

pattern_data = priority_customers.copy()


# Calculate percentile thresholds among
# customers with anomalous transactions

discount_threshold = (
    pattern_data["Average_Discount"]
    .quantile(0.75)
)

shipping_threshold = (
    pattern_data["Average_Shipping_Ratio"]
    .quantile(0.75)
)

margin_threshold = (
    pattern_data["Average_Profit_Margin"]
    .quantile(0.25)
)


def classify_pattern(row):

    discount_problem = (
        row["Average_Discount"]
        >= discount_threshold
    )

    shipping_problem = (
        row["Average_Shipping_Ratio"]
        >= shipping_threshold
    )

    margin_problem = (
        row["Average_Profit_Margin"]
        <= margin_threshold
    )

    # Count major risk factors
    problem_count = sum([
        discount_problem,
        shipping_problem,
        margin_problem
    ])

    if problem_count >= 2:
        return "MULTI_FACTOR"

    elif discount_problem:
        return "DISCOUNT_DRIVEN"

    elif shipping_problem:
        return "SHIPPING_DRIVEN"

    elif margin_problem:
        return "MARGIN_DRIVEN"

    else:
        return "GENERAL_PROFITABILITY"


pattern_data["Leakage_Pattern"] = (
    pattern_data.apply(
        classify_pattern,
        axis=1
    )
)


# ============================================
# DISPLAY PATTERN DISTRIBUTION
# ============================================

print("\n============================================")
print("LEAKAGE PATTERN ANALYSIS")
print("============================================")

print("\nPattern distribution:")

print(
    pattern_data["Leakage_Pattern"]
    .value_counts()
)


print("\nTop priority customers with patterns:")

print(
    pattern_data[
        [
            "Customer ID",
            "Risk_Score",
            "Risk_Category",
            "Potential_Loss",
            "Anomaly_Rate",
            "Average_Discount",
            "Average_Profit_Margin",
            "Average_Shipping_Ratio",
            "Leakage_Pattern"
        ]
    ]
    .sort_values(
        by="Risk_Score",
        ascending=False
    )
    .head(20)
)

# ============================================
# 19. RECOMMENDATION ENGINE
# ============================================

def generate_recommendation(pattern):

    if pattern == "DISCOUNT_DRIVEN":

        return (
            "Replace blanket discounts with targeted "
            "offers, minimum-order promotions, or "
            "customer-specific incentives."
        )

    elif pattern == "SHIPPING_DRIVEN":

        return (
            "Reduce shipping-cost pressure through "
            "minimum-order thresholds, larger-basket "
            "incentives, and fulfillment optimization."
        )

    elif pattern == "MARGIN_DRIVEN":

        return (
            "Promote higher-margin products and reduce "
            "incentives on products with consistently "
            "low or negative margins."
        )

    elif pattern == "MULTI_FACTOR":

        return (
            "Apply a combined profitability strategy: "
            "reduce excessive discounts, optimize "
            "shipping, and prioritize higher-margin "
            "products."
        )

    else:

        return (
            "Review customer product mix and transaction "
            "economics before applying additional "
            "discounts or promotions."
        )


pattern_data["Recommendation"] = (
    pattern_data["Leakage_Pattern"]
    .apply(generate_recommendation)
)


# ============================================
# 20. RECOMMENDATION PRIORITY
# ============================================

def recommendation_priority(row):

    if row["Risk_Category"] == "CRITICAL":
        return "IMMEDIATE"

    elif row["Risk_Category"] == "HIGH":
        return "HIGH"

    else:
        return "MONITOR"


pattern_data["Recommendation_Priority"] = (
    pattern_data.apply(
        recommendation_priority,
        axis=1
    )
)


# ============================================
# 21. DISPLAY RECOMMENDATIONS
# ============================================

print("\n============================================")
print("RECOMMENDATION ENGINE")
print("============================================")

print(
    "\nRecommendation distribution:"
)

print(
    pattern_data["Leakage_Pattern"]
    .value_counts()
)


print("\nTop 20 customer recommendations:")

print(
    pattern_data[
        [
            "Customer ID",
            "Risk_Score",
            "Risk_Category",
            "Potential_Loss",
            "Leakage_Pattern",
            "Recommendation",
            "Recommendation_Priority"
        ]
    ]
    .sort_values(
        by="Risk_Score",
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)

# ============================================
# 22. EXPLAINABLE RECOMMENDATIONS
# ============================================

def get_driver(row):

    pattern = row["Leakage_Pattern"]

    if pattern == "DISCOUNT_DRIVEN":
        return "Excessive discount pressure"

    elif pattern == "SHIPPING_DRIVEN":
        return "High shipping-cost pressure"

    elif pattern == "MARGIN_DRIVEN":
        return "Low or negative profit margin"

    elif pattern == "MULTI_FACTOR":
        return "Multiple profitability pressures"

    else:
        return "General profitability weakness"


def create_evidence(row):

    return (
        f"Anomaly rate: {row['Anomaly_Rate']:.1%}; "
        f"Average discount: {row['Average_Discount']:.1%}; "
        f"Average profit margin: {row['Average_Profit_Margin']:.1%}; "
        f"Average shipping ratio: {row['Average_Shipping_Ratio']:.1%}; "
        f"Potential loss: ₹{row['Potential_Loss']:,.2f}"
    )


pattern_data["Primary_Driver"] = (
    pattern_data.apply(
        get_driver,
        axis=1
    )
)

pattern_data["Evidence"] = (
    pattern_data.apply(
        create_evidence,
        axis=1
    )
)


# ============================================
# FINAL RECOMMENDATION VIEW
# ============================================

recommendation_view = pattern_data[
    [
        "Customer ID",
        "Risk_Score",
        "Risk_Category",
        "Potential_Loss",
        "Anomaly_Rate",
        "Leakage_Pattern",
        "Primary_Driver",
        "Evidence",
        "Recommendation",
        "Recommendation_Priority"
    ]
].copy()


print("\n============================================")
print("EXPLAINABLE RECOMMENDATION ENGINE")
print("============================================")

print(
    recommendation_view
    .sort_values(
        by="Risk_Score",
        ascending=False
    )
    .head(10)
    .to_string(index=False)
)

# ============================================
# 23. ANOMALOUS-TRANSACTION EVIDENCE
# ============================================

# Keep only transactions flagged by the 95% threshold
anomalous_transactions = customer_data[
    customer_data["Anomaly"] == 1
].copy()


# Aggregate ONLY anomalous transactions by customer
anomaly_profiles = (
    anomalous_transactions
    .groupby("Customer ID")
    .agg(
        Anomaly_Sales=("Sales", "sum"),
        Anomaly_Profit=("Profit", "sum"),
        Anomaly_Avg_Discount=("Discount", "mean"),
        Anomaly_Avg_Profit_Margin=("Profit Margin", "mean"),
        Anomaly_Avg_Shipping_Ratio=("Shipping Ratio", "mean")
    )
    .reset_index()
)


# Merge anomalous-transaction characteristics
# with our existing customer recommendation data
final_recommendations = pattern_data.merge(
    anomaly_profiles,
    on="Customer ID",
    how="left"
)


print("\n============================================")
print("FINAL ANOMALOUS-TRANSACTION EVIDENCE")
print("============================================")


print(
    final_recommendations[
        [
            "Customer ID",
            "Risk_Score",
            "Risk_Category",
            "Leakage_Pattern",
            "Anomalous_Orders",
            "Anomaly_Sales",
            "Anomaly_Profit",
            "Anomaly_Avg_Discount",
            "Anomaly_Avg_Profit_Margin",
            "Anomaly_Avg_Shipping_Ratio"
        ]
    ]
    .sort_values(
        by="Risk_Score",
        ascending=False
    )
    .head(10)
    .to_string(index=False)
)

# ============================================
# 24. SIX-MONTH IMPACT SIMULATION
# ============================================

print("\n============================================")
print("6-MONTH BUSINESS IMPACT SIMULATION")
print("============================================")


# --------------------------------------------
# 1. IDENTIFIED POTENTIAL LOSS
# --------------------------------------------

total_potential_loss = (
    final_recommendations["Potential_Loss"]
    .sum()
)


# --------------------------------------------
# 2. SALES FROM TARGET CUSTOMERS
# --------------------------------------------

total_target_sales = (
    final_recommendations["Total_Sales"]
    .sum()
)


print(
    f"\nPotential loss exposure: "
    f"₹{total_potential_loss:,.2f}"
)

print(
    f"Target customer sales: "
    f"₹{total_target_sales:,.2f}"
)


# --------------------------------------------
# 3. SCENARIO ASSUMPTIONS
# --------------------------------------------

scenarios = {

    "Conservative": {
        "loss_recovery": 0.10,
        "sales_uplift": 0.02
    },

    "Moderate": {
        "loss_recovery": 0.20,
        "sales_uplift": 0.05
    },

    "Aggressive": {
        "loss_recovery": 0.30,
        "sales_uplift": 0.08
    }
}


simulation_results = []


# --------------------------------------------
# 4. SIX-MONTH PROJECTION
# --------------------------------------------

for scenario_name, assumptions in scenarios.items():

    monthly_loss_recovery = (
        total_potential_loss
        * assumptions["loss_recovery"]
        / 6
    )

    monthly_incremental_sales = (
        total_target_sales
        * assumptions["sales_uplift"]
        / 6
    )

    monthly_total_impact = (
        monthly_loss_recovery
        + monthly_incremental_sales
    )

    cumulative_recovery = 0
    cumulative_sales = 0
    cumulative_total = 0


    for month in range(1, 7):

        cumulative_recovery += (
            monthly_loss_recovery
        )

        cumulative_sales += (
            monthly_incremental_sales
        )

        cumulative_total += (
            monthly_total_impact
        )


        simulation_results.append({

            "Scenario":
                scenario_name,

            "Month":
                month,

            "Profit_Recovery":
                monthly_loss_recovery,

            "Incremental_Sales":
                monthly_incremental_sales,

            "Total_Business_Impact":
                monthly_total_impact,

            "Cumulative_Profit_Recovery":
                cumulative_recovery,

            "Cumulative_Incremental_Sales":
                cumulative_sales,

            "Cumulative_Business_Impact":
                cumulative_total
        })


simulation_df = pd.DataFrame(
    simulation_results
)


# --------------------------------------------
# 5. DISPLAY RESULTS
# --------------------------------------------

print("\n6-MONTH PROJECTION:")

print(
    simulation_df.to_string(
        index=False
    )
)

# ============================================
# 25. FINAL DASHBOARD DATA
# ============================================

dashboard_data = final_recommendations.copy()

dashboard_data = dashboard_data.sort_values(
    by="Risk_Score",
    ascending=False
)

print("\n============================================")
print("FINAL DASHBOARD DATA")
print("============================================")

print("Rows:", dashboard_data.shape[0])
print("Columns:", dashboard_data.shape[1])


# ============================================
# 26. EXPORT FINAL RESULTS
# ============================================

dashboard_data.to_csv(
    "dashboard_data.csv",
    index=False
)

simulation_df.to_csv(
    "simulation_results.csv",
    index=False
)

print("\n============================================")
print("FINAL FILES EXPORTED")
print("============================================")

print("✓ dashboard_data.csv")
print("✓ simulation_results.csv")

