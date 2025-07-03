# telegram/bot.py

import os
import time
import csv
from collections import Counter
from collections import defaultdict

import telebot
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, BALANCE_LOG_PATH, TRADE_LOG_PATH, JOURNAL_PATH
from logger.balance_tracker import load_last_balance

bot = telebot.TeleBot(TELEGRAM_TOKEN)

COMMANDS_LIST = """
📊 TitanBot-Paper Telegram Commands:
/balance - Show current paper balance
/lasttrade - Show the most recent trade
/summary - Show today's performance summary
/log - Show last closed trade (log)
/journal - Show last journal entry
/rating - Show win/loss stats from ML log ✅
/journalstats - Show win rates and PnL per symbol ✅

"""

@bot.message_handler(commands=['start', 'help'])
def help_msg(message):
    bot.send_message(message.chat.id, COMMANDS_LIST)

@bot.message_handler(commands=['balance'])
def balance(message):
    balance = load_last_balance()
    bot.send_message(message.chat.id, f"💰 Current paper balance: ${balance:.2f}")

@bot.message_handler(commands=['lasttrade'])
def last_trade(message):
    if not os.path.exists(TRADE_LOG_PATH):
        bot.send_message(message.chat.id, "No trades yet.")
        return
    with open(TRADE_LOG_PATH, "r") as f:
        lines = f.readlines()
        if len(lines) < 2:
            bot.send_message(message.chat.id, "No trades yet.")
        else:
            bot.send_message(message.chat.id, f"📈 Last trade log:\n{lines[-1]}")

@bot.message_handler(commands=['log'])
def trade_log(message):
    if not os.path.exists(TRADE_LOG_PATH):
        bot.send_message(message.chat.id, "No trade log yet.")
        return
    with open(TRADE_LOG_PATH, "r") as f:
        lines = f.readlines()
        if len(lines) > 1:
            bot.send_message(message.chat.id, f"🧾 Trade log (last closed):\n{lines[-1]}")
        else:
            bot.send_message(message.chat.id, "No closed trades in log yet.")

@bot.message_handler(commands=['journal'])
def journal(message):
    if not os.path.exists(JOURNAL_PATH):
        bot.send_message(message.chat.id, "No journal entries yet.")
        return
    with open(JOURNAL_PATH, "r") as f:
        lines = f.readlines()
        if len(lines) > 1:
            bot.send_message(message.chat.id, f"📘 Journal (last):\n{lines[-1]}")
        else:
            bot.send_message(message.chat.id, "No journal entries yet.")

@bot.message_handler(commands=["summary"])
def summary(message):
    from datetime import datetime
    import pandas as pd
    import os

    journal_path = "logs/journal.csv"  # update path if needed
    if not os.path.exists(journal_path):
        bot.send_message(message.chat.id, "📄 No journal file found.")
        return

    df = pd.read_csv(journal_path)

    if "timestamp" not in df.columns or "pnl" not in df.columns:
        bot.send_message(message.chat.id, "❌ Journal file missing required fields.")
        return

    # Filter today's trades
    today_str = datetime.now().strftime("%Y-%m-%d")
    df["date"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d")
    today_trades = df[df["date"] == today_str]

    if today_trades.empty:
        bot.send_message(message.chat.id, f"📊 No trades yet for {today_str}.")
        return

    wins = (today_trades["pnl"] > 0).sum()
    losses = (today_trades["pnl"] < 0).sum()
    pnl_sum = today_trades["pnl"].sum() * 100

    bot.send_message(
        message.chat.id,
        f"📊 Summary for {today_str}:\n"
        f"✅ Wins: {wins}\n"
        f"❌ Losses: {losses}\n"
        f"📈 Total PnL: {pnl_sum:.2f}%",
    )

@bot.message_handler(commands=['journalstats'])
def handle_journal_stats(message):
    log_file = "ml_log.csv"

    if not os.path.exists(log_file):
        bot.reply_to(message, "No ML trades logged yet.")
        return

    with open(log_file, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        bot.reply_to(message, "No trade data available.")
        return

    symbol_stats = defaultdict(lambda: {
        "tp3": 0, "tp12": 0, "sl": 0, "other": 0, "pnl": 0.0, "count": 0
    })

    for row in rows:
        symbol = row["symbol"]
        reason = row["exit_reason"]
        pnl = float(row.get("pnl_pct", 0))

        symbol_stats[symbol]["count"] += 1
        symbol_stats[symbol]["pnl"] += pnl

        if "TP3" in reason:
            symbol_stats[symbol]["tp3"] += 1
        elif "TP" in reason:
            symbol_stats[symbol]["tp12"] += 1
        elif "SL" in reason:
            symbol_stats[symbol]["sl"] += 1
        else:
            symbol_stats[symbol]["other"] += 1

    # Compose response
    response = "📘 TitanBot Journal Stats:\n"

    for symbol, stats in symbol_stats.items():
        total = stats["count"]
        win = stats["tp3"] + stats["tp12"]
        win_rate = (win / total) * 100 if total else 0
        avg_pnl = stats["pnl"] / total if total else 0

        response += (
            f"\n🔹 {symbol} ({total} trades)\n"
            f"  - 🏆 TP3: {stats['tp3']}\n"
            f"  - 🎯 TP1–2: {stats['tp12']}\n"
            f"  - 💥 SL: {stats['sl']}\n"
            f"  - ❓ Other: {stats['other']}\n"
            f"  - ✅ Win Rate: {win_rate:.1f}%\n"
            f"  - 💰 Avg PnL: {avg_pnl*100:.2f}%\n"
        )

    bot.reply_to(message, response)


@bot.message_handler(commands=['rating'])
def handle_rating(message):
    log_file = "ml_log.csv"
    max_rows = 50

    if not os.path.exists(log_file):
        bot.reply_to(message, "No ML trades logged yet.")
        return

    rows = []
    with open(log_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        bot.reply_to(message, "No trade data available.")
        return

    rows = rows[-max_rows:]  # last N trades

    counts = Counter()
    total_pnl = 0.0

    for row in rows:
        reason = row["exit_reason"]
        pnl = float(row.get("pnl_pct", 0))
        total_pnl += pnl

        if "TP3" in reason:
            counts["tp3"] += 1
        elif "TP" in reason:
            counts["partial_tp"] += 1
        elif "SL" in reason:
            counts["sl"] += 1
        else:
            counts["other"] += 1

    total = sum([counts["tp3"], counts["partial_tp"], counts["sl"], counts["other"]])
    win_total = counts["tp3"] + counts["partial_tp"]
    win_rate = (win_total / total) * 100 if total > 0 else 0

    response = (
        f"📊 TitanBot Stats (Last {total} Trades):\n"
        f"🏆 TP3 Wins: {counts['tp3']}\n"
        f"🎯 TP1–2 Wins: {counts['partial_tp']}\n"
        f"💥 SL Losses: {counts['sl']}\n"
        f"🤷 Other: {counts['other']}\n"
        f"✅ Win Rate: {win_rate:.1f}%\n"
        f"💰 Total PnL: {total_pnl * 100:.2f}%"
    )

    bot.reply_to(message, response)

def run_telegram_polling():
    bot.infinity_polling()

def send_startup_notice():
    bot.send_message(TELEGRAM_CHAT_ID, "🤖 TitanBot-Paper has started.\n" + COMMANDS_LIST)
