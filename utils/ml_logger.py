# ml_logger.py

import csv
import os
from datetime import datetime
from utils.pnl_utils import calc_realistic_pnl

ML_LOG_FILE = "ml_log.csv"

def log_ml_features(trade, trend, volatility, atr):
    if trade.get("status") != "closed":
        return

    try:
        entry_price = float(trade.get("entry_price"))
        exit_price = float(trade.get("exit_price"))
        side = trade.get("side", "").upper()
        leverage = float(trade.get("leverage", 1))

        pnl_pct = calc_realistic_pnl(entry_price, exit_price, side, leverage)

        balance_snapshot = trade.get("balance_snapshot", 1000)
        risk_per_trade = 0.02
        raw_risk = balance_snapshot * risk_per_trade
        raw_profit = round(raw_risk * pnl_pct / 100, 4)

        duration = round(float(trade.get("closed_time", 0)) - float(trade.get("entry_time", 0)), 2)

    except Exception as e:
        print(f"⚠️ ML log calc error: {e}")
        return

    tp = trade.get("tp", [])
    row = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "id": trade.get("trade_id", ""),
        "symbol": trade.get("symbol", ""),
        "side": side,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "exit_reason": trade.get("exit_reason", ""),
        "sl": trade.get("sl", ""),
        "tp1": tp[0] if len(tp) > 0 else "",
        "tp2": tp[1] if len(tp) > 1 else "",
        "tp3": tp[2] if len(tp) > 2 else "",
        "atr": round(atr, 5),
        "trend_strength": round(trend, 5),
        "volatility": round(volatility, 5),
        "adx": round(trade.get("adx", 0.0), 5),
        "rsi": round(trade.get("rsi", 0.0), 5),
        "macd": round(trade.get("macd", 0.0), 5),
        "ema_ratio": round(trade.get("ema_ratio", 1.0), 5),
        "pnl_pct": pnl_pct,
        "raw_profit": raw_profit,
        "duration_sec": duration,
        "strategy": trade.get("strategy", ""),
        "leverage": leverage,
        "is_partial": 1 if "Partial" in trade.get("exit_reason", "") else 0
    }


    headers = list(row.keys())
    file_exists = os.path.isfile(ML_LOG_FILE)

    with open(ML_LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
