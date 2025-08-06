# engine/trade_tracker.py

from config import *
from core.indicator_utils import fetch_recent_candles, calculate_atr
from engine.position_model import build_fake_trade, update_position_status
from logger.trade_logger import log_exit
from logger.journal_writer import update_journal
from logger.balance_tracker import load_last_balance, update_balance
from utils.pnl_utils import calc_realistic_pnl
from utils.ml_logger import log_ml_features
from utils.terminal_logger import tlog


def maybe_open_new_trade(signal, candle, open_trades, fallback_atr=0.0):
    symbol = signal["symbol"]
    if any(t["symbol"] == symbol and t["status"] == "open" for t in open_trades):
        return None

    df = fetch_recent_candles(symbol)
    if df is None:
        tlog(f"❌ No candle data to open trade for {symbol}")
        return None

    tlog(f"✅ Successfully fetched {len(df)} candles for {symbol}")

    atr = calculate_atr(df)
    if not atr or atr == 0:
        atr = fallback_atr
        tlog(f"⚠️ Using fallback ATR for {symbol}: {atr:.5f}")
        if not atr or atr == 0:
            return None

    tlog(f"📐 {symbol} ATR: {atr:.5f}")

    trade = build_fake_trade(signal, candle, atr)
    if not trade:
        tlog(f"❌ Failed to create trade for {symbol}")
        return None

    tlog(f"📈 Fake trade opened: {trade['symbol']} {trade['side']} @ {trade['entry_price']}")
    return trade


def check_open_trades(open_trades, current_candle):
    still_open = []
    just_closed = []

    for trade in open_trades:
        updated = update_position_status(trade, current_candle)

        if updated["exit_reason"] == "TP1–2":
            pnl_check = calc_realistic_pnl(
                updated.get("entry_price"),
                updated.get("exit_price"),
                updated.get("side"),
                updated.get("leverage", 1)
            )
            if pnl_check < 0.1:
                tlog(f"⚠️ Skipping ML log for TP1–2 with tiny PnL: {pnl_check:.5f}%")
                continue

        # ✅ Partial TP balance logic
        num_hits = len(updated.get("hit", []))
        if num_hits > 0 and "partial_credit" not in updated and updated["status"] != "closed":
            partial_pct = 0.33 * num_hits  # TP1 = 33%, TP1+TP2 = 66%
            updated["partial_credit"] = True

            pnl_pct = calc_realistic_pnl(
                updated.get("entry_price"),
                updated["tp"][updated["hit"][-1]],
                updated.get("side"),
                updated.get("leverage", 1)
            )

            last_balance = load_last_balance()
            risk_amount = last_balance * RISK_PER_TRADE
            gain = risk_amount * pnl_pct / 100 * partial_pct
            new_balance = last_balance + gain

            update_balance(new_balance)
            tlog(f"💡 Partial TP balance applied ({partial_pct:.0%}): +{gain:.2f} → {new_balance:.2f}")

        # ✅ Final closure
        if updated["status"] == "closed":
            tlog(f"🚪 {updated['symbol']} closed due to {updated.get('exit_reason')} @ {updated.get('exit_price')}")

            last_balance = load_last_balance()
            pnl_pct = calc_realistic_pnl(
                updated.get("entry_price"),
                updated.get("exit_price"),
                updated.get("side"),
                updated.get("leverage", 1)
            )
            updated["pnl"] = pnl_pct  # 🔁 Store for logging

            risk_amount = last_balance * RISK_PER_TRADE
            profit_or_loss = risk_amount * pnl_pct / 100
            new_balance = last_balance + profit_or_loss
            update_balance(new_balance)

            tlog(f"🧠 Logging ML trade: {updated['symbol']} | Reason: {updated['exit_reason']} | PnL: {pnl_pct:+.5f}")
            tlog(f"💰 Balance updated: {last_balance:.2f} → {new_balance:.2f} ({pnl_pct:+.2f}%)")

            update_journal(updated)
            log_exit(updated)
            log_ml_features(
                updated,
                updated.get("trend_strength", 0),
                updated.get("volatility", 0),
                updated.get("atr", 0),
            )
            just_closed.append(updated["symbol"])
        else:
            still_open.append(updated)

    return still_open, just_closed
