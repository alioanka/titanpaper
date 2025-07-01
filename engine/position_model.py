# engine/position_model.py

import time
import uuid
from config import TP_MULTIPLIERS, SL_MULTIPLIER, TRAILING_START_AFTER_TP, TRAILING_GAP_ATR

def build_fake_trade(signal, candle, atr):
    entry = candle["close"]
    side = signal["direction"]
    sl = entry - atr * SL_MULTIPLIER if side == "LONG" else entry + atr * SL_MULTIPLIER
    tp_levels = [
        entry + atr * mult if side == "LONG" else entry - atr * mult
        for mult in TP_MULTIPLIERS
    ]

    return {
        "trade_id": str(uuid.uuid4())[:8],
        "symbol": signal["symbol"],
        "side": side,
        "entry_time": time.time(),
        "entry_price": entry,
        "sl": sl,
        "tp": tp_levels,
        "trailing": {
            "enabled": False,
            "triggered": False,
            "sl": None,
            "sl_gap": atr * TRAILING_GAP_ATR
        },
        "status": "open",
        "hit": [],
        "pnl": 0.0,
        "exit_reason": None
    }


def update_position_status(trade, candle):
    price = candle["close"]
    side = trade["side"]
    is_long = side == "LONG"

    if trade["status"] != "open":
        return trade

    # === SL Hit ===
    if (is_long and price <= trade["sl"]) or (not is_long and price >= trade["sl"]):
        trade["exit_price"] = trade["sl"]
        trade["status"] = "closed"
        trade["exit_reason"] = "SL"
        return trade

    # === TP Hits ===
    for i, tp in enumerate(trade["tp"]):
        if i in trade["hit"]:
            continue
        if (is_long and price >= tp) or (not is_long and price <= tp):
            trade["hit"].append(i)
            print(f"🎯 TP{i+1} hit: {trade['symbol']} {side} @ {tp:.2f}")
            if i == len(trade["tp"]) - 1:
                trade["exit_price"] = tp
                trade["status"] = "closed"
                trade["exit_reason"] = f"TP{i+1}"
                return trade
            if i >= TRAILING_START_AFTER_TP:
                trade["trailing"]["enabled"] = True

    # === Trailing SL Logic ===
    if trade["trailing"]["enabled"]:
        trail = trade["trailing"]
        if not trail["triggered"]:
            trail["triggered"] = True
            trail["sl"] = price - trail["sl_gap"] if is_long else price + trail["sl_gap"]
        else:
            new_sl = price - trail["sl_gap"] if is_long else price + trail["sl_gap"]
            if (is_long and new_sl > trail["sl"]) or (not is_long and new_sl < trail["sl"]):
                trail["sl"] = new_sl

        # Check trailing SL hit
        if (is_long and price <= trail["sl"]) or (not is_long and price >= trail["sl"]):
            trade["exit_price"] = price
            trade["status"] = "closed"
            trade["exit_reason"] = "TrailingSL"
            return trade

    return trade
