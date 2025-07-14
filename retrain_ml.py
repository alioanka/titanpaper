import pandas as pd
import numpy as np
import xgboost as xgb
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Load data
df = pd.read_csv('ml_log.csv')

# Basic columns always required
required_cols = ['exit_reason', 'pnl_pct', 'atr', 'trend_strength', 'volatility']

# Optional new features
optional_cols = ['adx', 'rsi', 'macd', 'ema_ratio']

# Filter available optional features
available_optional_cols = [col for col in optional_cols if col in df.columns]

# Drop rows with missing basic columns
df = df.dropna(subset=required_cols)

# Balance dataset
min_size = df['exit_reason'].value_counts().min()
balanced_df = df.groupby('exit_reason').apply(lambda x: x.sample(min_size, random_state=42)).reset_index(drop=True)

# Encode categorical
le_exit = LabelEncoder()
balanced_df['exit_reason_enc'] = le_exit.fit_transform(balanced_df['exit_reason'])
balanced_df['symbol_enc'] = LabelEncoder().fit_transform(balanced_df['symbol'])
balanced_df['side_enc'] = LabelEncoder().fit_transform(balanced_df['side'])

# Final feature list
feature_cols = ['symbol_enc', 'side_enc', 'entry_price', 'atr', 'trend_strength', 'volatility', 'duration_sec'] + available_optional_cols

# Prepare data
X = balanced_df[feature_cols]
y_class = balanced_df['exit_reason_enc']
y_reg = balanced_df['pnl_pct']

# Train/test split
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_class, test_size=0.2, random_state=42)
X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X, y_reg, test_size=0.2, random_state=42)

# Train XGBoost classifier
clf = xgb.XGBClassifier(objective='multi:softprob', eval_metric='mlogloss', use_label_encoder=False)
clf.fit(X_train_c, y_train_c)
clf.save_model('xgb_classifier.model')

# Train LightGBM regressor
reg = lgb.LGBMRegressor(objective='regression')
reg.fit(X_train_r, y_train_r)
reg.booster_.save_model('lgb_regressor.txt')

print("✅ Retrained models saved!")
