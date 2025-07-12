import pandas as pd
import numpy as np
import xgboost as xgb
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv('ml_log.csv')
df = df[df['exit_reason'] != '']  # clean empty labels

# Balance dataset
min_count = df['exit_reason'].value_counts().min()
balanced_df = df.groupby('exit_reason').apply(lambda x: x.sample(min_count)).reset_index(drop=True)

le_exit = LabelEncoder()
balanced_df['exit_reason_enc'] = le_exit.fit_transform(balanced_df['exit_reason'])
balanced_df['symbol_enc'] = LabelEncoder().fit_transform(balanced_df['symbol'])
balanced_df['side_enc'] = LabelEncoder().fit_transform(balanced_df['side'])

features = ['symbol_enc', 'side_enc', 'entry_price', 'atr', 'adx', 'rsi', 'macd', 'volatility', 'duration_sec']
X = balanced_df[features]
y_class = balanced_df['exit_reason_enc']
y_reg = balanced_df['pnl_pct']

X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_class, test_size=0.2, random_state=42)
X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X, y_reg, test_size=0.2, random_state=42)

clf = xgb.XGBClassifier(objective='multi:softprob', eval_metric='mlogloss', use_label_encoder=False)
clf.fit(X_train_c, y_train_c)
clf.save_model('xgb_classifier.model')

reg = lgb.LGBMRegressor(objective='regression')
reg.fit(X_train_r, y_train_r)
reg.booster_.save_model('lgb_regressor.txt')

print("✅ Models retrained on balanced dataset and saved!")
