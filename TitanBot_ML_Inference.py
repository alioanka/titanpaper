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

# === Prepare label encoder (same as training) ===
le_exit = LabelEncoder()
le_exit.fit(data['exit_reason'])

# === Encode categorical features ===
data['symbol_enc'] = LabelEncoder().fit_transform(data['symbol'])
data['side_enc'] = LabelEncoder().fit_transform(data['side'])

# === Features ===
features = ['symbol_enc', 'side_enc', 'entry_price', 'atr', 'trend_strength', 'volatility', 'duration_sec']

# === Select latest row (or loop over batch if desired) ===
latest = data[features].iloc[-1:]

# === Predict exit_reason (classification) ===
pred_class_probs = clf.predict_proba(latest)[0]
pred_class_idx = np.argmax(pred_class_probs)
pred_class_label = le_exit.inverse_transform([pred_class_idx])[0]
pred_class_confidence = pred_class_probs[pred_class_idx]

# === Predict expected pnl_pct (regression) ===
pred_pnl = reg.predict(latest)[0]

# === Print results ===
print("\n=== TitanBot ML Prediction ===")
print(f"Predicted Exit Reason: {pred_class_label}")
print(f"Confidence: {pred_class_confidence:.2%}")
print(f"Expected PnL (%): {pred_pnl:.2f}%")

# === Risk Recommendation ===
if pred_class_label in ['TP3', 'TP2-Partial'] and pred_class_confidence > 0.7:
    risk_advice = "✅ Strong signal → Consider higher position / leverage."
elif pred_class_label == 'SL' or pred_class_confidence < 0.5:
    risk_advice = "⚠️ Weak signal → Consider skipping or using minimal size."
else:
    risk_advice = "⚖️ Medium confidence → Use normal size."

print(f"Risk Advice: {risk_advice}")
