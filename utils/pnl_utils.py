# File: utils/pnl_utils.py

def calc_fake_pnl(trade):
    """ Return fake %PnL based on entry and exit price """
    try:
        entry = float(trade.get("entry_price", 0))
        exit_ = float(trade.get("exit_price", 0))
        side = trade.get("side", "").upper()

        if entry == 0 or exit_ == 0 or side not in ["LONG", "SHORT"]:
            return 0.0

        if side == "LONG":
            return (exit_ - entry) / entry
        else:
            return (entry - exit_) / entry
    except Exception as e:
        print(f"[PnL Error] {e}")
        return 0.0
