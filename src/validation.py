#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Data validation and quality checks module"""
import numpy as np
import pandas as pd


def validate_basic_data(X_train, y_train, X_test, y_test, feature_names):
    """Validate basic data properties"""
    print("\n============================================================")
    print("DATA AND MODEL VALIDATION")
    print("============================================================")
    print("\n=== Basic Validation (training) ===")
    print(f"Shape: {X_train.shape}")
    print(f"Missing values: {np.isnan(X_train).sum()}")
    print(f"Duplicates: {len(X_train) - len(np.unique(X_train, axis=0))}")
    print(f"Class distribution: {dict(zip(*np.unique(y_train, return_counts=True)))}")
    print(f"Default rate: {y_train.mean()*100:.2f}% defaults")
    print("\n=== Basic Validation (test) ===")
    print(f"Shape: {X_test.shape}")
    print(f"Missing values: {np.isnan(X_test).sum()}")
    print(f"Duplicates: {len(X_test) - len(np.unique(X_test, axis=0))}")
    print(f"Class distribution: {dict(zip(*np.unique(y_test, return_counts=True)))}")
    print(f"Default rate: {y_test.mean()*100:.2f}% defaults")


def detect_data_drift(X_train, X_test, feature_names):
    """Detect data drift between train and test sets"""
    print("\n=== Data Drift Detection ===")
    drift_features = []
    for i, feature in enumerate(feature_names):
        train_mean = X_train[:, i].mean()
        test_mean = X_test[:, i].mean()
        train_std = X_train[:, i].std()
        test_std = X_test[:, i].std()
        if train_mean != 0:
            mean_drift = abs((test_mean - train_mean) / train_mean) * 100
        else:
            mean_drift = 0
        if train_std != 0:
            std_drift = abs((test_std - train_std) / train_std) * 100
        else:
            std_drift = 0
        if mean_drift > 10 or std_drift > 10:
            drift_features.append({'feature': feature, 'mean_drift': mean_drift, 'std_drift': std_drift})
    if drift_features:
        print("\nFeatures with significant drift (>10%):")
        for item in drift_features[:5]:
            print(f"  {item['feature']}: mean drift = {item['mean_drift']:.2f}%, std drift = {item['std_drift']:.2f}%")
    else:
        print("No significant drift detected")


def validate_feature_statistics(X_train, X_test, feature_names):
    """Validate feature statistics"""
    print("\n=== Feature Statistics (training) ===")
    print(f"{'Feature':<30} {'Mean':>10} {'Std':>10} {'Outliers':>10}")
    print("-" * 50)
    for i, feature in enumerate(feature_names):
        mean = X_train[:, i].mean()
        std = X_train[:, i].std()
        outliers = np.sum(np.abs(X_train[:, i] - mean) > 3 * std) / len(X_train) * 100
        print(f"{feature:<30} {mean:>10.2f} {std:>10.2f} {outliers:>9.2f}%")
    print("\n=== Feature Statistics (test) ===")
    print(f"{'Feature':<30} {'Mean':>10} {'Std':>10} {'Outliers':>10}")
    print("-" * 50)
    for i, feature in enumerate(feature_names):
        mean = X_test[:, i].mean()
        std = X_test[:, i].std()
        outliers = np.sum(np.abs(X_test[:, i] - mean) > 3 * std) / len(X_test) * 100
        print(f"{feature:<30} {mean:>10.2f} {std:>10.2f} {outliers:>9.2f}%")


def validate_labels(y_train, y_test):
    """Validate label distribution and quality"""
    print("\n=== Label Quality (training) ===")
    unique_labels = np.unique(y_train)
    print(f"Unique labels: {unique_labels}")
    distribution = pd.Series(y_train).value_counts()
    print(f"Label distribution:\n{distribution}")
    if len(unique_labels) > 1:
        imbalance = max(distribution) / min(distribution)
        print(f"Imbalance ratio: {imbalance:.2f}:1")
    print("\n=== Label Quality (test) ===")
    unique_labels = np.unique(y_test)
    print(f"Unique labels: {unique_labels}")
    distribution = pd.Series(y_test).value_counts()
    print(f"Label distribution:\n{distribution}")
    if len(unique_labels) > 1:
        imbalance = max(distribution) / min(distribution)
        print(f"Imbalance ratio: {imbalance:.2f}:1")


def validate_data_and_models(X_train, y_train, X_test, y_test, feature_names):
    """Run all data validation checks"""
    validate_basic_data(X_train, y_train, X_test, y_test, feature_names)
    detect_data_drift(X_train, X_test, feature_names)
    validate_feature_statistics(X_train, X_test, feature_names)
    validate_labels(y_train, y_test)
    return None
