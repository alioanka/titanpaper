# utils/pnl_utils.py
def calc_fake_pnl(trade):
    try:
        entry = float(trade["entry_price"])
        exit_price = float(trade.get("exit_price", 0))
        side = trade.get("side")
        reason = trade.get("exit_reason", "")
        if not entry or not exit_price:
            return 0.0

        change = (exit_price - entry) / entry
        pnl = change if side == "LONG" else -change

        # Simulated scaling — you can calibrate these
        if reason == "TP1":
            return round(pnl * 0.25, 5)
        elif reason == "TP1-2":
            return round(pnl * 0.5, 5)
        elif reason == "TP3":
            return round(pnl, 5)
        elif reason == "TrailingSL":
            return round(pnl * 0.75, 5)
        elif reason == "SL":
            return round(pnl, 5)
        else:
            return round(pnl, 5)

    except Exception as e:
        print(f"⚠️ calc_fake_pnl() error: {e} | trade={trade}")
        return 0.0
