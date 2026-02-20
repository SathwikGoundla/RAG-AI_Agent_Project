"""
Configuration module for Loan Default Prediction project
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# Model configuration
MODEL_CONFIG = {
    "random_state": 42,
    "test_size": 0.2,
    "val_size": 0.1,
}

# XGBoost parameters
XGBOOST_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": "auc",
    "max_depth": 6,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "n_estimators": 100,
    "random_state": 42,
}

# Random Forest parameters
RF_PARAMS = {
    "n_estimators": 100,
    "max_depth": 15,
    "min_samples_split": 10,
    "min_samples_leaf": 5,
    "random_state": 42,
    "n_jobs": -1,
}

# Feature engineering
CATEGORICAL_FEATURES = [
    "Gender",
    "Married",
    "Education",
    "Employment_Type",
    "LoanPurpose",
]

NUMERICAL_FEATURES = [
    "Age",
    "Monthly_Income",
    "Num_Credit_Products",
    "Num_Active_Loans",
    "Credit_Utilization_Ratio",
    "Total_Debt",
    "Requested_Loan_Amount",
    "Loan_Term_Months",
]

TARGET_COLUMN = "Default"

# Explainability
SHAP_RANDOM_STATE = 42
SHAP_SAMPLE_SIZE = 1000

# Neptune configuration
NEPTUNE_PROJECT = "workspace/@your-username/loan-default"
NEPTUNE_API_TOKEN = "your-api-token-here"
