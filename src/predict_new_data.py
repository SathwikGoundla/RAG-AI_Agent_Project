"""
Prediction script for new loan data using trained models
Uses the pre-trained XGBoost and Random Forest models to make predictions
"""

import pandas as pd
import numpy as np
import joblib
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')


class LoanPredictor:
    def __init__(self):
        """Initialize predictor with trained models"""
        self.model_dir = Path('models')
        self.xgb_model = joblib.load(self.model_dir / 'xgboost.pkl')
        self.rf_model = joblib.load(self.model_dir / 'random_forest.pkl')
        print("[OK] Models loaded successfully")

    def preprocess_data(self, df):
        """Preprocess new data to match training format"""
        df = df.copy()

        # Fill missing values
        df['Credit_History'].fillna(df['Credit_History'].mode()[0], inplace=True)
        df['Self_Employed'].fillna(df['Self_Employed'].mode()[0], inplace=True)
        df['Dependents'].fillna(df['Dependents'].mode()[0], inplace=True)
        df['Education'].fillna(df['Education'].mode()[0], inplace=True)
        df['LoanAmount'].fillna(df['LoanAmount'].median(), inplace=True)
        df['Loan_Amount_Term'].fillna(df['Loan_Amount_Term'].mode()[0], inplace=True)

        # Convert Dependents column: '3+' -> 3
        df['Dependents'] = df['Dependents'].astype(str).str.replace('+', '').astype(float)

        # Create features matching the training data
        df['Monthly_Income'] = df['ApplicantIncome'] + df['CoapplicantIncome']
        df['Debt_to_Income'] = df['LoanAmount'] / (df['Monthly_Income'] + 1)
        df['Credit_Utilization_Ratio'] = df['LoanAmount'] / (df['ApplicantIncome'] + 1)

        # Encode categorical variables
        df['Gender_encoded'] = (df['Gender'] == 'Female').astype(int)
        df['Married_encoded'] = (df['Married'] == 'Yes').astype(int)
        df['Education_encoded'] = (df['Education'] == 'Graduate').astype(int)
        df['Self_Employed_encoded'] = (df['Self_Employed'] == 'Yes').astype(int)
        df['Urban_encoded'] = (df['Property_Area'] == 'Urban').astype(int)
        df['Semiurban_encoded'] = (df['Property_Area'] == 'Semiurban').astype(int)

        # Select features for prediction
        feature_columns = [
            'Monthly_Income', 'Credit_History', 'LoanAmount',
            'Loan_Amount_Term', 'Gender_encoded', 'Married_encoded',
            'Education_encoded', 'Self_Employed_encoded', 'Dependents',
            'Urban_encoded', 'Semiurban_encoded', 'Debt_to_Income',
            'Credit_Utilization_Ratio'
        ]

        X = df[feature_columns].copy()

        # Feature scaling (normalize)
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=feature_columns)

        return X_scaled, df

    def predict(self, csv_path, output_path='predictions_output.csv'):
        """Make predictions on new data"""
        print(f"\n[LOAD] Loading dataset from: {csv_path}")

        # Load data
        df = pd.read_csv(csv_path)
        print(f"[OK] Loaded {len(df)} loan records")

        # Preprocess
        X_scaled, df_original = self.preprocess_data(df)
        print(f"[OK] Data preprocessed and scaled")

        # Make predictions
        xgb_pred = self.xgb_model.predict(X_scaled)
        rf_pred = self.rf_model.predict(X_scaled)

        xgb_proba = self.xgb_model.predict_proba(X_scaled)[:, 1]
        rf_proba = self.rf_model.predict_proba(X_scaled)[:, 1]

        # Ensemble prediction (average probability)
        ensemble_proba = (xgb_proba + rf_proba) / 2
        ensemble_pred = (ensemble_proba >= 0.5).astype(int)

        print(f"[OK] Predictions generated")

        # Create results dataframe
        results = pd.DataFrame({
            'Loan_ID': df_original['Loan_ID'],
            'Applicant_Income': df_original['ApplicantIncome'],
            'Loan_Amount': df_original['LoanAmount'],
            'Credit_History': df_original['Credit_History'],
            'XGBoost_Default_Prob': np.round(xgb_proba, 4),
            'XGBoost_Prediction': xgb_pred,
            'RandomForest_Default_Prob': np.round(rf_proba, 4),
            'RandomForest_Prediction': rf_pred,
            'Ensemble_Default_Prob': np.round(ensemble_proba, 4),
            'Ensemble_Prediction': ensemble_pred,
            'Final_Decision': ['success' if p < 0.5 else 'rejected' for p in ensemble_proba]
        })

        # Save results
        results.to_csv(output_path, index=False)
        print(f"[OK] Results saved to: {output_path}")

        return results

    def print_summary(self, results):
        """Print prediction summary"""
        print("\n" + "="*80)
        print("PREDICTION SUMMARY")
        print("="*80)

        total = len(results)
        approved = (results['Ensemble_Prediction'] == 0).sum()
        rejected = (results['Ensemble_Prediction'] == 1).sum()

        print(f"\nTotal Loan Applications: {total}")
        print(f"Success (Low Risk): {approved} ({100*approved/total:.1f}%)")
        print(f"Rejected (High Risk): {rejected} ({100*rejected/total:.1f}%)")

        print(f"\nAverage Default Probability: {results['Ensemble_Default_Prob'].mean():.4f}")
        print(f"Min Default Probability: {results['Ensemble_Default_Prob'].min():.4f}")
        print(f"Max Default Probability: {results['Ensemble_Default_Prob'].max():.4f}")

        print("\nSample Results (First 10):")
        print(results[['Loan_ID', 'Loan_Amount', 'Ensemble_Default_Prob', 'Final_Decision']].head(10).to_string(index=False))

        print("\n" + "="*80)


if __name__ == "__main__":
    # Initialize predictor
    predictor = LoanPredictor()

    # Make predictions on new dataset
    results = predictor.predict('loan_dataset.csv.csv', 'predictions_output.csv')

    # Print summary
    predictor.print_summary(results)

    print("\n[DONE] Prediction complete! Results saved to 'predictions_output.csv'")
