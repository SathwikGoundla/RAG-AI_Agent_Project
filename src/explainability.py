#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Explainability analysis using SHAP and LIME"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import REPORTS_DIR

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    import lime
    import lime.lime_tabular
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False


def generate_shap_analysis(model, X_train_sample, X_test, feature_names):
    """Generate SHAP explanations"""
    print("\n--- SHAP Analysis ---")
    print("\n=== Generating SHAP Explanations ===")
    if not SHAP_AVAILABLE:
        print("[FAIL] SHAP not available")
        return None, None
    try:
        explainer = shap.Explainer(model, X_train_sample)
        shap_values = explainer(X_test)
        print(f"[OK] SHAP values computed for {len(X_test)} samples")
        shap_importance = np.abs(shap_values.values).mean(axis=0)
        shap_importance_df = pd.DataFrame({
            'feature': feature_names,
            'shap_importance': shap_importance
        }).sort_values('shap_importance', ascending=False)
        print(f"\n=== Top 10 Important Features (SHAP) ===")
        print(shap_importance_df.head(10).to_string(index=False))
        return shap_values, shap_importance_df
    except Exception as e:
        print(f"[FAIL] Error in SHAP analysis: {e}")
        return None, None


def generate_lime_explanations(model, X_test, feature_names, num_samples=3):
    """Generate LIME explanations for individual predictions"""
    print("\n--- LIME Analysis ---")
    if not LIME_AVAILABLE:
        print("[FAIL] LIME not available")
        return
    try:
        explainer = lime.lime_tabular.LimeTabularExplainer(
            X_test,
            feature_names=feature_names,
            class_names=['No Default', 'Default'],
            mode='classification'
        )
        for idx in [0, len(X_test)//2, len(X_test)-1]:
            if idx >= len(X_test):
                continue
            exp = explainer.explain_instance(X_test[idx], model.predict_proba)
            exp_list = exp.as_list()
            features = [item[0] for item in exp_list]
            weights = [item[1] for item in exp_list]
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(features, weights, color=['green' if w > 0 else 'red' for w in weights])
            ax.set_xlabel('Feature Impact')
            ax.set_title(f'LIME Explanation - Sample {idx}')
            REPORTS_DIR.mkdir(exist_ok=True)
            plt.savefig(REPORTS_DIR / f'lime_explanation_sample_{idx}.png', dpi=300, bbox_inches='tight')
            print(f"[OK] LIME explanation plot saved to {REPORTS_DIR / f'lime_explanation_sample_{idx}.png'}")
            plt.close()
    except Exception as e:
        print(f"[FAIL] Error in LIME analysis: {e}")


def generate_explanations(xgb_model, rf_model, X_test, feature_names):
    """Generate all explainability analysis"""
    print("\n" + "="*70)
    print(" EXPLAINABILITY ANALYSIS")
    print("="*70)
    shap_values, shap_importance = generate_shap_analysis(
        xgb_model, X_test[:500] if len(X_test) > 500 else X_test, X_test, feature_names
    )
    generate_lime_explanations(xgb_model, X_test[:50] if len(X_test) > 50 else X_test, feature_names)
    return {"shap_values": shap_values, "shap_importance": shap_importance}
