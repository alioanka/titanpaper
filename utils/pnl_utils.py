# File: utils/pnl_utils.py

def calc_fake_pnl(trade):
    """Return realistic %PnL based on entry/exit and direction"""
    try:
        entry = float(trade.get("entry_price", 0))
        exit_ = float(trade.get("exit_price", 0))
        side = trade.get("side", "").upper()

        if entry <= 0 or exit_ <= 0 or side not in ["LONG", "SHORT"]:
            raise ValueError("Invalid entry/exit/side")

        # Raw return
        pnl = (exit_ - entry) / entry if side == "LONG" else (entry - exit_) / entry

        # Optional: cap extreme spikes
        if abs(pnl) > 0.10:
            print(f"⚠️ Unrealistic PnL ({pnl:.2%}) for trade: {trade}")
            return 0.0

        return round(pnl, 6)

    except Exception as e:
        print(f"[PnL Error] {e} | trade: {trade}")
        return 0.0

