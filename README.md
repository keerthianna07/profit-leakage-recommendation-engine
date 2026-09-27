# Profit Leakage Recommendation Engine

## Project Overview

The **Profit Leakage Recommendation Engine** is a deep-learning-based customer risk analysis and recommendation system designed to identify unusual customer transactions that may indicate profit leakage.

The system uses a **Deep Autoencoder** for anomaly detection and converts transaction-level anomalies into customer-level business insights. Customers are assigned risk scores, classified into leakage patterns, and provided with explainable recommendations.

The project also includes a **6-month business impact simulation** and an interactive dashboard.

## Problem Statement

In an e-commerce environment, profitability can be reduced by excessive discounts, high shipping costs, low or negative profit margins, and combinations of multiple profitability pressures.

The objective is to detect such patterns automatically and provide actionable recommendations for improving customer profitability.

## Objectives

1. Detect anomalous transactions using deep learning.
2. Identify customers associated with potential profit leakage.
3. Calculate customer-level risk scores.
4. Classify customers into leakage patterns.
5. Generate explainable, pattern-specific recommendations.
6. Provide evidence supporting each recommendation.
7. Estimate potential business impact over six months.
8. Present results through an interactive dashboard.

## Dataset

The project uses an e-commerce transaction dataset stored at:

```text
Data/ECOMM DATA.xlsx
```

The dataset contains transaction-level information including sales, quantity, discount, shipping cost, profit, customer information, product information, market information, and order details.

## Technologies Used

- Python
- Pandas
- NumPy
- TensorFlow / Keras
- Scikit-learn
- OpenPyXL
- HTML
- CSS
- JavaScript
- Chart.js

## Project Workflow

```text
E-commerce Transaction Data
          ↓
Data Cleaning
          ↓
Feature Engineering
          ↓
Feature Selection
          ↓
Categorical Encoding
          ↓
Train / Test Split
          ↓
Feature Scaling
          ↓
Deep Autoencoder
          ↓
Reconstruction Error
          ↓
95th Percentile Anomaly Threshold
          ↓
Anomalous Transactions
          ↓
Customer-Level Aggregation
          ↓
Customer Risk Score
          ↓
Leakage Pattern Classification
          ↓
Recommendation Engine
          ↓
Explainable Recommendations
          ↓
Business Impact Simulation
          ↓
Interactive Dashboard
```

## 1. Data Cleaning and Feature Engineering

The project removes the `Postal Code` column when present and converts `Order Date` and `Ship Date` to datetime values.

The following business features are engineered:

### Profit Margin

```text
Profit Margin = Profit / Sales
```

### Shipping Ratio

```text
Shipping Ratio = Shipping Cost / Sales
```

### Discount Impact

```text
Discount Impact = Discount × Sales
```

### Delivery Time

```text
Delivery Time = Ship Date - Order Date
```

Missing values in the engineered features are filled with zero.

## 2. Model Features

### Numerical Features

- Sales
- Quantity
- Discount
- Shipping Cost
- Profit
- Profit Margin
- Shipping Ratio
- Discount Impact
- Delivery Time

### Categorical Features

- Ship Mode
- Segment
- Market
- Region
- Category
- Sub-Category
- Order Priority

Categorical variables are converted using one-hot encoding.

## 3. Deep Autoencoder

A Deep Autoencoder is used for unsupervised anomaly detection.

Architecture:

```text
Input
  ↓
Dense(32, ReLU)
  ↓
Dense(16, ReLU)
  ↓
Dense(8, ReLU)
  ↓
Dense(16, ReLU)
  ↓
Dense(32, ReLU)
  ↓
Output
```

The model learns to reconstruct the input transaction feature vector. Transactions with larger reconstruction errors are considered more unusual.

## 4. Reconstruction Error and Anomaly Detection

Mean Squared Error is calculated between each original scaled transaction and its reconstruction:

```text
Reconstruction Error = Mean((Original - Reconstructed)²)
```

The project compares the following percentile thresholds:

```text
90%, 92.5%, 95%, 97.5%, 99%
```

The **95th percentile** is used as the tentative operational threshold. Transactions whose reconstruction error exceeds this threshold are flagged as anomalous.

## 5. Customer Profit-Leakage Profile

Transaction-level anomalies are aggregated by `Customer ID`.

The system calculates:

- Total Orders
- Total Sales
- Total Profit
- Negative Profit Orders
- Anomalous Orders
- Anomaly Rate
- Average Discount
- Average Profit Margin
- Average Shipping Ratio
- Total Discount Impact
- Potential Loss

### Anomaly Rate

```text
Anomaly Rate = Anomalous Orders / Total Orders
```

### Potential Loss

Potential loss is calculated from negative-profit transactions associated with each customer.

## 6. Customer Risk Scoring

Four component risk scores are calculated:

1. Anomaly Risk
2. Loss Risk
3. Discount Risk
4. Shipping Risk

The combined score is:

```text
Risk Score =
0.35 × Anomaly Risk
+ 0.35 × Loss Risk
+ 0.15 × Discount Risk
+ 0.15 × Shipping Risk
```

Risk categories:

| Risk Score | Category |
|---:|---|
| 75 or above | CRITICAL |
| 50–74.99 | HIGH |
| 25–49.99 | MEDIUM |
| Below 25 | LOW |

## 7. Leakage Pattern Classification

Customers are classified using:

- Average Discount
- Average Shipping Ratio
- Average Profit Margin

The system identifies five patterns:

### GENERAL_PROFITABILITY
General profitability weakness without a dominant single driver.

### MULTI_FACTOR
Multiple profitability pressures are present.

### SHIPPING_DRIVEN
High shipping-cost pressure is the primary issue.

### DISCOUNT_DRIVEN
Excessive discount pressure is the primary issue.

### MARGIN_DRIVEN
Low or negative profit margin is the primary issue.

## 8. Recommendation Engine

Recommendations are generated according to the leakage pattern.

**Discount Driven:** Replace blanket discounts with targeted offers, minimum-order promotions, or customer-specific incentives.

**Shipping Driven:** Reduce shipping-cost pressure through minimum-order thresholds, larger-basket incentives, and fulfillment optimization.

**Margin Driven:** Promote higher-margin products and reduce incentives on products with consistently low or negative margins.

**Multi Factor:** Apply a combined profitability strategy by reducing excessive discounts, optimizing shipping, and prioritizing higher-margin products.

**General Profitability:** Review customer product mix and transaction economics before applying additional discounts or promotions.

## 9. Explainable Recommendations

Each recommendation can include:

- Primary Driver
- Anomaly Rate
- Average Discount
- Average Profit Margin
- Average Shipping Ratio
- Potential Loss
- Recommendation
- Recommendation Priority

This connects the recommendation to measurable customer-level evidence.

## 10. Anomalous-Transaction Evidence

For transactions flagged by the selected threshold, the system aggregates:

- Anomaly Sales
- Anomaly Profit
- Average Anomalous Discount
- Average Anomalous Profit Margin
- Average Anomalous Shipping Ratio

This provides supporting evidence for the customer recommendations.

## 11. Six-Month Business Impact Simulation

Three scenarios are simulated:

| Scenario | Loss Recovery | Sales Uplift |
|---|---:|---:|
| Conservative | 10% | 2% |
| Moderate | 20% | 5% |
| Aggressive | 30% | 8% |

The simulation calculates monthly and cumulative:

- Profit Recovery
- Incremental Sales
- Total Business Impact

These are scenario-based estimates, not guaranteed financial outcomes.

## 12. Dashboard

The dashboard contains:

### KPI Cards
- Customers Analyzed
- Critical Customers
- Potential Loss Exposure
- Target Customer Sales

### Customer Risk Analysis
Visual distribution across Critical, High, Medium, and Low risk categories.

### Profit Leakage Patterns
Distribution across the five leakage patterns.

### Priority Customer Recommendations
Top customers by risk score with their potential loss, leakage pattern, recommendation, and priority.

### 6-Month Business Impact
Comparison of Conservative, Moderate, and Aggressive projected cumulative business impact.

## 13. Current Dashboard Results

| Metric | Value |
|---|---:|
| Customers Analyzed | 389 |
| Critical Customers | 153 |
| Potential Loss Exposure | ₹1,02,248.27 |
| Target Customer Sales | ₹11,58,427.44 |

Current leakage-pattern distribution:

| Leakage Pattern | Customers |
|---|---:|
| GENERAL_PROFITABILITY | 205 |
| MULTI_FACTOR | 91 |
| SHIPPING_DRIVEN | 64 |
| DISCOUNT_DRIVEN | 16 |
| MARGIN_DRIVEN | 13 |

## 14. Project Structure

```text
profit-leakage-recommendation-engine/
│
├── main.py
├── README.md
├── dashboard_data.csv
├── simulation_results.csv
│
├── Data/
│   └── ECOMM DATA.xlsx
│
└── dashboard/
    ├── index.html
    ├── script.js
    └── style.css
```

## 15. How to Run

Install the required Python packages:

```bash
pip install pandas numpy tensorflow scikit-learn openpyxl
```

Run the ML pipeline:

```bash
python main.py
```

This generates:

```text
dashboard_data.csv
simulation_results.csv
```

Then open the dashboard through a local web server or the development server being used for the project:

```text
dashboard/index.html
```

## 16. Business Value

The project transforms raw transaction data into an actionable profitability workflow:

```text
Detect
  ↓
Prioritize
  ↓
Explain
  ↓
Recommend
  ↓
Estimate Impact
  ↓
Visualize
```

Rather than only identifying unusual transactions, the system connects anomalies to customer risk, potential financial exposure, likely leakage drivers, recommended actions, and projected business impact.

## 17. Important Notes

The anomaly detector is an **unsupervised Deep Autoencoder**. The negative-profit indicator is used as a business proxy for evaluating detected anomalies; it is not the training target of the autoencoder.

The 95th-percentile threshold is an operational choice based on threshold comparison and business considerations.

The six-month impact values are scenario simulations based on explicit recovery and sales-uplift assumptions.

## Author

**Keerthi Anna**

B.Tech — Computer Science Engineering (Data Science)

## Project Status

**Completed** — Core ML pipeline, anomaly detection, customer risk scoring, leakage classification, recommendation engine, explainability layer, business simulation, CSV exports, and interactive dashboard implemented.
