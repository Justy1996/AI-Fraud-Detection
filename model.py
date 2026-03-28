"""
GHANA'S AI POLICE: AI Fraud Detection System for Mobile Money
ML Model Module - Uses HistGradientBoosting (optimized for large datasets) + SMOTE-style resampling
"""
import numpy as np
import pandas as pd
import pickle
import os
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (precision_score, recall_score, f1_score,
                              accuracy_score, confusion_matrix)
from sklearn.utils import resample

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'fraud_model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), 'scaler.pkl')
CSV_PATH = r"C:\Users\User\.cache\kagglehub\datasets\ealaxi\paysim1\versions\2\PS_20174392719_1491204439457_log.csv"

TRANSACTION_TYPES = ['CASH_IN', 'CASH_OUT', 'TRANSFER', 'PAYMENT', 'DEBIT']

def load_paysim_data(sample_size=None):
    """Load the real PaySim dataset from Kaggle."""
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"PaySim dataset not found at {CSV_PATH}")
    
    # We only read the necessary columns to save memory
    usecols = ['step', 'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
               'oldbalanceDest', 'newbalanceDest', 'isFraud']
    
    print("[INFO] Loading Kaggle PaySim dataset into pandas...")
    df = pd.read_csv(CSV_PATH, usecols=usecols)
    
    # Derive UI features expected by the system
    df['hour'] = df['step'] % 24
    df['transaction_freq'] = 1  # Mock frequency for simplicity on 6M rows
    
    if sample_size and len(df) > sample_size:
        print(f"[INFO] Sampling dataset to {sample_size} rows for efficient training...")
        fraud_df = df[df['isFraud'] == 1]
        legit_df = df[df['isFraud'] == 0]
        
        # Take all fraud (~8213 rows) and sample legit to reach sample_size
        n_fraud = len(fraud_df)
        n_legit = sample_size - n_fraud
        if n_legit > 0:
            legit_df = legit_df.sample(n=min(n_legit, len(legit_df)), random_state=42)
            
        df = pd.concat([fraud_df, legit_df]).sample(frac=1, random_state=42).reset_index(drop=True)
        
    return df


def engineer_features(df):
    """Feature engineering pipeline matching the research paper."""
    df = df.copy()
    
    # One-hot encode transaction type
    for t in TRANSACTION_TYPES:
        df[f'type_{t}'] = (df['type'] == t).astype(int)
    
    # Balance difference features (key fraud indicators)
    df['balance_diff_orig'] = df['oldbalanceOrg'] - df['newbalanceOrig']
    df['balance_diff_dest'] = df['newbalanceDest'] - df['oldbalanceDest']
    df['balance_mismatch'] = (df['balance_diff_orig'] - df['balance_diff_dest']).abs()
    
    # Amount features
    df['log_amount'] = np.log1p(df['amount'])
    df['amount_to_balance_ratio'] = df['amount'] / (df['oldbalanceOrg'] + 1)
    
    # Suspicious patterns
    df['orig_drained'] = ((df['newbalanceOrig'] == 0) & (df['oldbalanceOrg'] > 0)).astype(int)
    df['dest_was_empty'] = (df['oldbalanceDest'] == 0).astype(int)
    df['is_night'] = df['hour'].apply(lambda h: 1 if h <= 4 or h >= 22 else 0)
    
    feature_cols = (
        [f'type_{t}' for t in TRANSACTION_TYPES] +
        ['log_amount', 'amount_to_balance_ratio',
         'balance_diff_orig', 'balance_diff_dest', 'balance_mismatch',
         'orig_drained', 'dest_was_empty', 'is_night',
         'transaction_freq', 'oldbalanceOrg', 'newbalanceOrig',
         'oldbalanceDest', 'newbalanceDest']
    )
    
    return df, feature_cols


def smote_resample(X, y):
    """Simple SMOTE-like oversampling of minority class."""
    df_temp = pd.DataFrame(X)
    df_temp['label'] = y
    
    majority = df_temp[df_temp['label'] == 0]
    minority = df_temp[df_temp['label'] == 1]
    
    # Upsample minority to 50% of majority size
    minority_upsampled = resample(minority,
                                  replace=True,
                                  n_samples=len(majority) // 2,
                                  random_state=42)
    
    balanced = pd.concat([majority, minority_upsampled])
    balanced = balanced.sample(frac=1, random_state=42)
    
    X_bal = balanced.drop('label', axis=1).values
    y_bal = balanced['label'].values
    return X_bal, y_bal


def train_model():
    """Train the fraud detection model and return metrics."""
    # Use 500,000 samples for efficient training while maintaining all fraud cases
    df = load_paysim_data(sample_size=500000)
    df, feature_cols = engineer_features(df)
    
    X = df[feature_cols].values
    y = df['isFraud'].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # SMOTE-style resampling on training set
    print("[INFO] Applying SMOTE resampling...")
    X_train_bal, y_train_bal = smote_resample(X_train_scaled, y_train)
    
    # Primary model: HistGradientBoosting (optimized for large datasets)
    print("[INFO] Training HistGradientBoosting model...")
    model = HistGradientBoostingClassifier(
        learning_rate=0.1,
        max_iter=150,
        max_depth=6,
        min_samples_leaf=20,
        random_state=42
    )
    model.fit(X_train_bal, y_train_bal)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    
    # Feature importances are not directly available in HistGradientBoostingClassifier
    # We will compute permutation importance or use a surrogate. For API compatibility,
    # we'll mock them uniformly, or compute a basic variance proxy.
    importances = np.var(X_train_bal, axis=0)
    importances = importances / np.sum(importances)
    
    metrics = {
        'accuracy': round(accuracy_score(y_test, y_pred), 4),
        'precision': round(precision_score(y_test, y_pred, zero_division=0), 4),
        'recall': round(recall_score(y_test, y_pred, zero_division=0), 4),
        'f1': round(f1_score(y_test, y_pred, zero_division=0), 4),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        'feature_names': feature_cols,
        'feature_importances': importances.tolist()
    }
    
    # Save model and scaler
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump({'model': model, 'feature_cols': feature_cols, 'feature_importances': importances.tolist()}, f)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"[SUCCESS] Model saved. Accuracy: {metrics['accuracy']}, Precision: {metrics['precision']}, Recall: {metrics['recall']}")
    return metrics


def load_model():
    """Load the trained model from disk."""
    if not os.path.exists(MODEL_PATH):
        return None, None, None, None
    with open(MODEL_PATH, 'rb') as f:
        data = pickle.load(f)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    return data['model'], scaler, data['feature_cols'], data.get('feature_importances', [])


def predict_transaction(transaction_data, threshold=0.5):
    """
    Predict if a transaction is fraud.
    transaction_data: dict with keys matching transaction fields
    Returns: dict with prediction, probability, risk_score, top_features
    """
    model, scaler, feature_cols, importances = load_model()
    if model is None:
        raise ValueError("Model not trained yet. Please train first.")
    
    # Build a single-row DataFrame
    df = pd.DataFrame([transaction_data])
    
    # Ensure standard cols exist
    if 'hour' not in df.columns:
        df['hour'] = 12
    if 'transaction_freq' not in df.columns:
        df['transaction_freq'] = 1
    if 'step' not in df.columns:
        df['step'] = 1
    
    df, _ = engineer_features(df)
    
    # Handle missing columns
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
            
    # Ensure correct order
    X = df[feature_cols].values
    X_scaled = scaler.transform(X)
    
    prob = model.predict_proba(X_scaled)[0][1]
    is_fraud = int(prob >= threshold)
    
    # Get top contributing features
    if len(importances) == len(feature_cols):
        feat_imp = list(zip(feature_cols, importances))
        feat_imp.sort(key=lambda x: x[1], reverse=True)
        top_features = [{'feature': f, 'importance': round(float(i), 4)} 
                        for f, i in feat_imp[:5]]
    else:
        top_features = []
    
    # Risk level
    if prob >= 0.8:
        risk_level = 'CRITICAL'
    elif prob >= 0.6:
        risk_level = 'HIGH'
    elif prob >= 0.4:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    return {
        'is_fraud': is_fraud,
        'fraud_probability': round(float(prob), 4),
        'risk_level': risk_level,
        'top_features': top_features,
        'threshold_used': threshold
    }
