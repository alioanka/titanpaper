# main.py

import time
import uuid
from config import *
from data.price_feed import get_latest_candle
from core.signal_engine import generate_signal
from engine.trade_tracker import check_open_trades, maybe_open_new_trade
from logger.trade_logger import log_trade
from logger.journal_writer import update_journal
from telegram.bot import run_telegram_polling, send_startup_notice
from threading import Thread

# In-memory store of fake open trades
open_trades = []

def run_bot():
    print(f"🚀 Starting {BOT_NAME} in {MODE.upper()} mode...")
    print("🔄 Sending Telegram startup notice...")
    send_startup_notice()
    print("✅ Telegram startup notice sent. Starting loop...")


    while True:
        for symbol in SYMBOLS:
            try:
                candle = get_latest_candle(symbol, TIMEFRAME)
                print(f"🧠 {symbol} Candle fetched: O={candle['open']} C={candle['close']} H={candle['high']} L={candle['low']}")

                if not candle:
                    print(f"⚠️ Skipping {symbol}: no candle data")
                    continue

                # Step 1: Check existing trades for SL/TP/Trailing hits
                global open_trades
                open_trades = check_open_trades(open_trades, candle)

                # Step 2: If no open trade for symbol, generate signal
                is_open = any(t['symbol'] == symbol and t['status'] == 'open' for t in open_trades)
                if not is_open:
                    signal = generate_signal(symbol, candle)
                    if signal:
                        print(f"✅ TRADE SIGNAL: {symbol} | Side: {signal['direction']} | Trend: {signal['confidence']:.4f} | Price: {candle['close']}")

                        trade = maybe_open_new_trade(signal, candle, open_trades)
                        if trade:
                            trade["strategy"] = signal.get("strategy_name", DEFAULT_STRATEGY_NAME)
                            trade["id"] = str(uuid.uuid4())
                            open_trades.append(trade)
                            log_trade(trade)
                    else:
                        print(f"❌ No valid signal for {symbol}")

            except Exception as e:
                print(f"❌ Error for {symbol}: {e}")

        # Wait before next cycle
        time.sleep(EVALUATION_INTERVAL)


if __name__ == "__main__":
    Thread(target=run_telegram_polling, daemon=True).start()
    run_bot()
