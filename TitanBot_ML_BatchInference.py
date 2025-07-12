import pandas as pd
import numpy as np
import xgboost as xgb
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder

# === Load models ===
clf = xgb.XGBClassifier()
clf.load_model('xgb_classifier.model')

reg = lgb.Booster(model_file='lgb_regressor.txt')

# === Load recent data ===
data = pd.read_csv('ml_log.csv')

# === Prepare label encoder ===
le_exit = LabelEncoder()
le_exit.fit(data['exit_reason'])

# === Encode categorical features ===
data['symbol_enc'] = LabelEncoder().fit_transform(data['symbol'])
data['side_enc'] = LabelEncoder().fit_transform(data['side'])

# === Features ===
features = ['symbol_enc', 'side_enc', 'entry_price', 'atr', 'trend_strength', 'volatility', 'duration_sec']

# === Select last N rows ===
N = 5
latest_batch = data[features].tail(N)

# === Predict ===
pred_class_probs = clf.predict_proba(latest_batch)
pred_class_idx = np.argmax(pred_class_probs, axis=1)
pred_class_labels = le_exit.inverse_transform(pred_class_idx)
pred_class_confidence = np.max(pred_class_probs, axis=1)
pred_pnls = reg.predict(latest_batch)

print("\n=== TitanBot ML Batch Prediction ===")
for i in range(N):
    print(f"\nRow {i+1}:")
    print(f"Predicted Exit Reason: {pred_class_labels[i]}")
    print(f"Confidence: {pred_class_confidence[i]:.2%}")
    print(f"Expected PnL (%): {pred_pnls[i]:.2f}%")
    if pred_class_labels[i] in ['TP3', 'TP2-Partial'] and pred_class_confidence[i] > 0.7:
        advice = "✅ Strong signal → Consider higher position / leverage."
    elif pred_class_labels[i] == 'SL' or pred_class_confidence[i] < 0.5:
        advice = "⚠️ Weak signal → Consider skipping or using minimal size."
    else:
        advice = "⚖️ Medium confidence → Use normal size."
    print(f"Risk Advice: {advice}")
