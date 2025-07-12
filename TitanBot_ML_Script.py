import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error, r2_score
import lightgbm as lgb
import xgboost as xgb
import matplotlib.pyplot as plt

# === Load data ===
ml_log = pd.read_csv('ml_log.csv')
journal = pd.read_csv('logs/journal.csv')

ml_log.dropna(inplace=True)
data = ml_log.copy()

# === Encode categorical features ===
data['symbol_enc'] = LabelEncoder().fit_transform(data['symbol'])
data['side_enc'] = LabelEncoder().fit_transform(data['side'])

# === Encode classification target ===
le_exit = LabelEncoder()
data['exit_reason_enc'] = le_exit.fit_transform(data['exit_reason'])

# === Features & targets ===
features = ['symbol_enc', 'side_enc', 'entry_price', 'atr', 'trend_strength', 'volatility', 'duration_sec']
X = data[features]
y_class = data['exit_reason_enc']
y_reg = data['pnl_pct']

# === Split ===
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_class, test_size=0.2, random_state=42)
X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X, y_reg, test_size=0.2, random_state=42)

# === XGBoost Classifier ===
clf = xgb.XGBClassifier(objective='multi:softprob', eval_metric='mlogloss', use_label_encoder=False)
clf.fit(X_train_c, y_train_c)
y_pred_c = clf.predict(X_test_c)
y_pred_c_labels = le_exit.inverse_transform(y_pred_c)

print('\n--- Classification Report (XGBoost) ---')
print(classification_report(le_exit.inverse_transform(y_test_c), y_pred_c_labels))
print('Confusion Matrix:')
print(confusion_matrix(le_exit.inverse_transform(y_test_c), y_pred_c_labels))

xgb.plot_importance(clf)
plt.show()

# === LightGBM Regressor ===
reg = lgb.LGBMRegressor(objective='regression')
reg.fit(X_train_r, y_train_r)
y_pred_r = reg.predict(X_test_r)

mse = mean_squared_error(y_test_r, y_pred_r)
r2 = r2_score(y_test_r, y_pred_r)
print(f'\n--- Regression Results (LightGBM) ---\nMSE: {mse:.4f}, R2: {r2:.4f}')

lgb.plot_importance(reg)
plt.show()

# === Save models ===
clf.save_model('xgb_classifier.model')
reg.booster_.save_model('lgb_regressor.txt')

print('Models saved! Ready for integration.')
