def calc_fake_pnl(trade):
    if not trade.get("exit_price") or not trade.get("entry_price"):
        return 0.0

    entry = trade["entry_price"]
    exit = trade["exit_price"]
    side = trade["side"]

    if side == "LONG":
        return (exit - entry) / entry
    else:
        return (entry - exit) / entry
