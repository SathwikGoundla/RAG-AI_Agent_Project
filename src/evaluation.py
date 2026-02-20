#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Model evaluation and visualization module"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report
)
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import REPORTS_DIR


def compute_metrics(y_true, y_pred, y_proba):
    """Compute evaluation metrics"""
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1-Score": f1_score(y_true, y_pred, zero_division=0),
        "ROC-AUC": roc_auc_score(y_true, y_proba)
    }


def plot_roc_curves(models_dict, X_test, y_test, feature_names):
    """Plot ROC curves for all models"""
    fig, ax = plt.subplots(figsize=(10, 6))
    for model_name, model in models_dict.items():
        y_proba = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        auc = roc_auc_score(y_test, y_proba)
        label = f'{model_name.replace("_", " ").title()} (AUC={auc:.4f})'
        ax.plot(fpr, tpr, label=label, linewidth=2)
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC Curves - Model Comparison')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    REPORTS_DIR.mkdir(exist_ok=True)
    plt.savefig(REPORTS_DIR / 'roc_curves.png', dpi=300, bbox_inches='tight')
    print("[OK] ROC curves saved to", REPORTS_DIR / 'roc_curves.png')
    plt.close()


def plot_confusion_matrices(models_dict, X_test, y_test):
    """Plot confusion matrices for all models"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for idx, (model_name, model) in enumerate(models_dict.items()):
        y_pred = model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx], cbar=False)
        axes[idx].set_title(f'{model_name.replace("_", " ").title()} Confusion Matrix')
        axes[idx].set_xlabel('Predicted')
        axes[idx].set_ylabel('Actual')
    plt.tight_layout()
    REPORTS_DIR.mkdir(exist_ok=True)
    plt.savefig(REPORTS_DIR / 'confusion_matrices.png', dpi=300, bbox_inches='tight')
    print("[OK] Confusion matrices saved to", REPORTS_DIR / 'confusion_matrices.png')
    plt.close()


def plot_feature_importance(models_dict, feature_names):
    """Plot feature importance for all models"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    for idx, (model_name, model) in enumerate(models_dict.items()):
        importances = model.feature_importances_
        indices = np.argsort(importances)[-10:]
        sorted_features = [feature_names[i] for i in indices]
        sorted_importances = importances[indices]
        axes[idx].barh(sorted_features, sorted_importances, color='steelblue')
        axes[idx].set_xlabel('Importance')
        axes[idx].set_title(f'{model_name.replace("_", " ").title()} - Top 10 Features')
    plt.tight_layout()
    REPORTS_DIR.mkdir(exist_ok=True)
    plt.savefig(REPORTS_DIR / 'feature_importance_comparison.png', dpi=300, bbox_inches='tight')
    print("[OK] Feature importance comparison saved to", REPORTS_DIR / 'feature_importance_comparison.png')
    plt.close()


def plot_model_comparison(comparison_df):
    """Plot model comparison metrics"""
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(comparison_df))
    width = 0.15
    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    for i, metric in enumerate(metrics):
        ax.bar(x + i*width, comparison_df[metric], width, label=metric)
    ax.set_xlabel('Model')
    ax.set_ylabel('Score')
    ax.set_title('Model Comparison - All Metrics')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(comparison_df['Model'])
    ax.legend()
    ax.set_ylim([0.75, 1.0])
    ax.grid(True, alpha=0.3, axis='y')
    REPORTS_DIR.mkdir(exist_ok=True)
    plt.savefig(REPORTS_DIR / 'model_comparison.png', dpi=300, bbox_inches='tight')
    print("[OK] Model comparison plot saved to", REPORTS_DIR / 'model_comparison.png')
    plt.close()


def evaluate_all_models(xgb_model, rf_model, X_test, y_test, feature_names):
    """Evaluate all models and generate visualizations"""
    print("\n" + "="*70)
    print(" EVALUATING MODELS")
    print("="*70)
    models_dict = {"xgboost": xgb_model, "random_forest": rf_model}
    results = []
    for model_name, model in models_dict.items():
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        metrics = compute_metrics(y_test, y_pred, y_proba)
        print(f"\n=== {model_name.replace('_', ' ').upper()} ===")
        print("\nMetrics:")
        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, zero_division=0))
        results.append({"Model": model_name.replace("_", " ").title(), **metrics})
    comparison_df = pd.DataFrame(results)
    print("\nGenerating visualizations...")
    plot_roc_curves(models_dict, X_test, y_test, feature_names)
    plot_confusion_matrices(models_dict, X_test, y_test)
    plot_feature_importance(models_dict, feature_names)
    plot_model_comparison(comparison_df)
    print(f"\n=== Model Comparison ===")
    print(comparison_df.to_string(index=False))
    return None, comparison_df
