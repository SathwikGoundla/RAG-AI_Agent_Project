#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Data loading and preprocessing module"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import (
    DATA_DIR,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
)


def create_sample_dataset(n_samples=1000):
    """Create sample loan dataset"""
    np.random.seed(42)
    data = {
        "Age": np.random.randint(20, 70, n_samples),
        "Gender": np.random.choice(["Male", "Female"], n_samples),
        "Married": np.random.choice(["Yes", "No"], n_samples),
        "Education": np.random.choice(["High School","Bachelor","Master","PhD"], n_samples),
        "Employment_Type": np.random.choice(["Salaried","Self-Employed","Unemployed"], n_samples),
        "Monthly_Income": np.random.exponential(5000, n_samples) + 2000,
        "Num_Credit_Products": np.random.randint(0, 10, n_samples),
        "Num_Active_Loans": np.random.randint(0, 5, n_samples),
        "Credit_Utilization_Ratio": np.random.uniform(0, 100, n_samples),
        "Total_Debt": np.random.exponential(10000, n_samples),
        "LoanPurpose": np.random.choice(["Home","Car","Education","Personal"], n_samples),
        "Requested_Loan_Amount": np.random.exponential(50000, n_samples) + 10000,
        "Loan_Term_Months": np.random.choice([12, 24, 36, 48, 60], n_samples),
    }
    df = pd.DataFrame(data)
    df[TARGET_COLUMN] = ((df["Monthly_Income"] < df["Monthly_Income"].median()) * 1 + (df["Num_Active_Loans"] > 2) * 1 + (df["Credit_Utilization_Ratio"] > 80) * 1 + (np.random.random(n_samples) < 0.2) * 1) > 1.5
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)
    return df


def load_data():
    """Load or create dataset"""
    dataset_path = DATA_DIR / "loan_data.csv"
    if dataset_path.exists():
        df = pd.read_csv(dataset_path)
        print(f"[OK] Loaded dataset from {dataset_path}")
    else:
        df = create_sample_dataset(n_samples=1000)
        df.to_csv(dataset_path, index=False)
        print(f"[OK] Created and saved sample dataset to {dataset_path}")
    return df


def preprocess_data(df):
    """Preprocess the dataset"""
    print("\n=== Data Preprocessing ===")
    print(f"\nMissing values:\n{df.isnull().sum()}")
    for col in NUMERICAL_FEATURES:
        if col in df.columns and df[col].isnull().any():
            df[col].fillna(df[col].median(), inplace=True)
    for col in CATEGORICAL_FEATURES:
        if col in df.columns and df[col].isnull().any():
            df[col].fillna(df[col].mode()[0], inplace=True)
    print(f"\nDataset shape: {df.shape}")
    print(f"Target distribution:\n{df[TARGET_COLUMN].value_counts()}")
    print(f"Target ratio: {df[TARGET_COLUMN].mean():.2%} defaults")
    return df


def split_data(df, test_size=0.2, val_size=0.1):
    """Split data into train, validation, and test sets"""
    print("\n=== Data Splitting ===")
    X = df.drop(TARGET_COLUMN, axis=1)
    y = df[TARGET_COLUMN]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=val_size, random_state=42, stratify=y_train)
    print(f"Training set size: {len(X_train)}")
    print(f"Validation set size: {len(X_val)}")
    print(f"Test set size: {len(X_test)}")
    print(f"Training set default %: {y_train.mean():.2%}")
    print(f"Test set default %: {y_test.mean():.2%}")
    return X_train, X_val, X_test, y_train, y_val, y_test


def balance_data(X_train, y_train):
    """Balance training data using SMOTE"""
    print("\n=== Data Balancing ===")
    print(f"Original training set distribution:")
    print(y_train.value_counts())
    smote = SMOTE(random_state=42)
    X_balanced, y_balanced = smote.fit_resample(X_train, y_train)
    print(f"Balanced training set distribution:")
    print(pd.Series(y_balanced).value_counts())
    return X_balanced, y_balanced


def scale_features(X_train, X_val, X_test):
    """Normalize features"""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_val_scaled, X_test_scaled


def encode_categorical(df):
    """Encode categorical variables"""
    df_encoded = df.copy()
    for col in CATEGORICAL_FEATURES:
        if col in df_encoded.columns:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
    return df_encoded


def prepare_data(df=None):
    """Complete data preparation pipeline"""
    if df is None:
        df = load_data()
    df = preprocess_data(df)
    df = encode_categorical(df)
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(df)
    X_train_bal, y_train_bal = balance_data(X_train, y_train)
    X_train_scaled, X_val_scaled, X_test_scaled = scale_features(X_train_bal, X_val, X_test)
    feature_names = list(X_train.drop(TARGET_COLUMN, axis=1).columns) if TARGET_COLUMN in X_train.columns else list(X_train.columns)
    print(f"\n[OK] Data preparation completed!")
    print(f"  - Training set: {X_train_scaled.shape}")
    print(f"  - Validation set: {X_val_scaled.shape}")
    print(f"  - Test set: {X_test_scaled.shape}")
    print(f"  - Features: {len(feature_names)}")
    return {
        "X_train": X_train_scaled,
        "X_val": X_val_scaled,
        "X_test": X_test_scaled,
        "y_train": y_train_bal.values,
        "y_val": y_val.values,
        "y_test": y_test.values,
        "feature_names": feature_names,
    }
