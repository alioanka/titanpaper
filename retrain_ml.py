import pandas as pd
import numpy as np
import xgboost as xgb
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Load data
ml_log = pd.read_csv('ml_log.csv')
ml_log.dropna(inplace=True)

# Encode
le_exit = LabelEncoder()
ml_log['exit_reason_enc'] = le_exit.fit_transform(ml_log['exit_reason'])
ml_log['symbol_enc'] = LabelEncoder().fit_transform(ml_log['symbol'])
ml_log['side_enc'] = LabelEncoder().fit_transform(ml_log['side'])

features = ['symbol_enc', 'side_enc', 'entry_price', 'atr', 'trend_strength', 'volatility', 'duration_sec']
X = ml_log[features]
y_class = ml_log['exit_reason_enc']
y_reg = ml_log['pnl_pct']

# Split
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_class, test_size=0.2, random_state=42)
X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X, y_reg, test_size=0.2, random_state=42)

# Train
clf = xgb.XGBClassifier(objective='multi:softprob', eval_metric='mlogloss', use_label_encoder=False)
clf.fit(X_train_c, y_train_c)
clf.save_model('xgb_classifier.model')

reg = lgb.LGBMRegressor(objective='regression')
reg.fit(X_train_r, y_train_r)
reg.booster_.save_model('lgb_regressor.txt')

print("✅ Models retrained and saved!")
