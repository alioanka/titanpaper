# engine/position_model.py

import time
import uuid
from config import TP_MULTIPLIERS, SL_MULTIPLIER, TRAILING_START_AFTER_TP, TRAILING_GAP_ATR

def build_fake_trade(signal, candle, atr):
    entry = candle["close"]
    side = signal["direction"]
    is_long = side == "LONG"

    # Base TP and SL calculations
    sl = entry - atr * SL_MULTIPLIER if is_long else entry + atr * SL_MULTIPLIER
    tp_levels = [
        entry + atr * mult if is_long else entry - atr * mult
        for mult in TP_MULTIPLIERS
    ]

    # === Optional Safety: Enforce minimum TP spread (e.g. 0.1%)
    MIN_TP_SPREAD = 0.001  # 0.1%
    spread = abs(tp_levels[0] - entry) / entry
    if spread < MIN_TP_SPREAD:
        scale = (entry * MIN_TP_SPREAD) / abs(tp_levels[0] - entry)
        tp_levels = [entry + (tp - entry) * scale for tp in tp_levels]
        sl = entry - (entry - sl) * scale if is_long else entry + (sl - entry) * scale

    print(f"📊 {signal['symbol']} trade setup → SL: {sl:.2f}, TP1: {tp_levels[0]:.2f}, TP2: {tp_levels[1]:.2f}, TP3: {tp_levels[2]:.2f}")

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
    high = candle["high"]
    low = candle["low"]
    side = trade["side"]
    is_long = side == "LONG"

    if trade["status"] != "open":
        return trade

    # === SL Hit (directional wick logic)
    sl_hit = (is_long and low <= trade["sl"]) or (not is_long and high >= trade["sl"])
    if sl_hit:
        trade["exit_price"] = trade["sl"]
        trade["status"] = "closed"
        trade["exit_reason"] = "SL"
        return trade

    # === TP Hits
    for i, tp in enumerate(trade["tp"]):
        if i in trade["hit"]:
            continue

        tp_hit = (is_long and high >= tp) or (not is_long and low <= tp)
        if tp_hit:
            trade["hit"].append(i)
            print(f"🎯 TP{i+1} hit: {trade['symbol']} {side} @ {tp:.2f}")

            if i == len(trade["tp"]) - 1:
                trade["exit_price"] = tp
                trade["status"] = "closed"
                trade["exit_reason"] = f"TP{i+1}"
                return trade

            if i >= TRAILING_START_AFTER_TP:
                trade["trailing"]["enabled"] = True

    # === Trailing SL
    if trade["trailing"]["enabled"]:
        trail = trade["trailing"]
        current_price = candle["close"]

        if not trail["triggered"]:
            trail["triggered"] = True
            trail["sl"] = current_price - trail["sl_gap"] if is_long else current_price + trail["sl_gap"]
        else:
            new_sl = current_price - trail["sl_gap"] if is_long else current_price + trail["sl_gap"]
            if (is_long and new_sl > trail["sl"]) or (not is_long and new_sl < trail["sl"]):
                trail["sl"] = new_sl

        # Trailing SL hit?
        if (is_long and low <= trail["sl"]) or (not is_long and high >= trail["sl"]):
            trade["exit_price"] = trail["sl"]
            trade["status"] = "closed"
            trade["exit_reason"] = "TrailingSL"
            return trade

    return trade


