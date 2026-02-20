#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Model training module"""
import joblib
import numpy as np
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import MODELS_DIR, XGBOOST_PARAMS, RF_PARAMS


def train_xgboost(X_train, y_train, X_val, y_val):
    """Train XGBoost model"""
    print("\nTraining XGBoost model...")
    xgb_model = XGBClassifier(
        max_depth=XGBOOST_PARAMS["max_depth"],
        learning_rate=XGBOOST_PARAMS["learning_rate"],
        n_estimators=XGBOOST_PARAMS["n_estimators"],
        random_state=42,
        eval_metric="logloss"
    )
    eval_set = [(X_val, y_val)]
    xgb_model.fit(X_train, y_train, eval_set=eval_set, verbose=False)
    return xgb_model


def train_random_forest(X_train, y_train, X_val, y_val):
    """Train Random Forest model"""
    print("Training Random Forest model...")
    rf_model = RandomForestClassifier(
        n_estimators=RF_PARAMS["n_estimators"],
        max_depth=RF_PARAMS["max_depth"],
        n_jobs=-1,
        random_state=42
    )
    rf_model.fit(X_train, y_train)
    return rf_model


def evaluate_model(model, X_test, y_test, model_name=""):
    """Evaluate model performance"""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    accuracy = (y_pred == y_test).mean()
    auc = roc_auc_score(y_test, y_proba)
    print(f"\n{model_name} Evaluation:")
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  AUC-ROC: {auc:.4f}")
    return {"model": model, "y_pred": y_pred, "y_proba": y_proba, "accuracy": accuracy, "auc": auc}


def train_models(X_train, y_train, X_val, y_val, feature_names):
    """Train all models"""
    print("\n" + "="*70)
    print(" TRAINING MODELS")
    print("="*70)
    xgb_model = train_xgboost(X_train, y_train, X_val, y_val)
    xgb_eval = evaluate_model(xgb_model, X_val, y_val, "XGBoost")
    rf_model = train_random_forest(X_train, y_train, X_val, y_val)
    rf_eval = evaluate_model(rf_model, X_val, y_val, "Random Forest")
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(xgb_model, MODELS_DIR / "xgboost.pkl")
    joblib.dump(rf_model, MODELS_DIR / "random_forest.pkl")
    print(f"\n[OK] Model saved to {MODELS_DIR / 'xgboost.pkl'}")
    print(f"[OK] Model saved to {MODELS_DIR / 'random_forest.pkl'}")
    return {"xgboost": xgb_model, "random_forest": rf_model, "xgboost_eval": xgb_eval, "random_forest_eval": rf_eval}
