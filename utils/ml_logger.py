import csv
import os
from datetime import datetime
from utils.pnl_utils import calc_fake_pnl


ML_LOG_FILE = "ml_log.csv"

def log_ml_features(trade, trend, volatility, atr):
    headers = [
        "timestamp", "symbol", "side", "entry_price", "sl", 
        "tp1", "tp2", "tp3", "atr", "trend_strength", 
        "volatility", "exit_price", "exit_reason", "pnl_pct"
    ]
    try:
        pnl_pct = round(float(calc_fake_pnl(trade)), 5)
    except Exception as e:
        print(f"⚠️ ML log PnL error: {e} | trade={trade}")
        pnl_pct = 0.0

    tp_list = trade.get("tp", [])
    tp1 = tp_list[0] if len(tp_list) > 0 else ""
    tp2 = tp_list[1] if len(tp_list) > 1 else ""
    tp3 = tp_list[2] if len(tp_list) > 2 else ""


    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": trade["symbol"],
        "side": trade["side"],
        "entry_price": trade["entry_price"],
        "sl": trade["sl"],
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "atr": round(atr, 5),
        "trend_strength": round(trend, 5),
        "volatility": round(volatility, 5),
        "exit_price": trade.get("exit_price", ""),
        "exit_reason": trade.get("exit_reason", ""),
        "pnl_pct": pnl_pct
    }

    file_exists = os.path.isfile(ML_LOG_FILE)
    with open(ML_LOG_FILE, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# You can import and reuse this anywhere:
# log_ml_features(trade, trend, volatility, atr)
