# utils/pnl_utils.py
def calc_realistic_pnl(entry_price, exit_price, side, leverage):
    if not entry_price or not exit_price:
        return 0.0
    try:
        entry_price = float(entry_price)
        exit_price = float(exit_price)
        pct = ((exit_price - entry_price) / entry_price) * 100
        if side.lower() == "short":
            pct *= -1
        return round(pct * leverage, 4)
    except Exception as e:
        print(f"[PnL Error] calc_realistic_pnl failed: {e}")
        return 0.0

