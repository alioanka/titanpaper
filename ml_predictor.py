import pandas as pd
import numpy as np
import xgboost as xgb
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder

# === Load models once ===
clf = xgb.XGBClassifier()
clf.load_model('xgb_classifier.model')
reg = lgb.Booster(model_file='lgb_regressor.txt')

# === Prepare encoders ===
symbol_encoder = LabelEncoder()
side_encoder = LabelEncoder()
exit_encoder = LabelEncoder()

def prepare_encoders(data_path='ml_log.csv'):
    data = pd.read_csv(data_path, on_bad_lines='skip')
    symbol_encoder.fit(data['symbol'])
    side_encoder.fit(data['side'])
    exit_encoder.fit(data['exit_reason'])

prepare_encoders()

def predict_trade(signal_data):
    features = {
        'symbol_enc': symbol_encoder.transform([signal_data['symbol']])[0],
        'side_enc': side_encoder.transform([signal_data['side']])[0],
        'entry_price': signal_data['entry_price'],
        'atr': signal_data['atr'],
        'trend_strength': signal_data['trend_strength'],
        'volatility': signal_data['volatility'],
        'duration_sec': signal_data['duration_sec'],
        'adx': signal_data['adx'],
        'rsi': signal_data['rsi'],
        'macd': signal_data['macd'],
        'ema_ratio': signal_data['ema_ratio']
    }

    df = pd.DataFrame([features])
    pred_class_probs = clf.predict_proba(df)[0]
    pred_class_idx = np.argmax(pred_class_probs)
    pred_class_label = exit_encoder.inverse_transform([pred_class_idx])[0]
    pred_class_confidence = pred_class_probs[pred_class_idx]
    pred_pnl = reg.predict(df)[0]

    return {
        'exit_reason': pred_class_label,
        'confidence': round(pred_class_confidence, 6),
        'expected_pnl': round(pred_pnl, 6)
    }
