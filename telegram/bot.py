# telegram/bot.py

import os
import time
import csv
from collections import Counter, defaultdict

import telebot
import pandas as pd

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
/rating - Show win/loss stats (last 50 from journal) ✅
/journalstats - Win rates and PnL per symbol (journal) ✅

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
    with open(TRADE_LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) < 2:
            bot.send_message(message.chat.id, "No trades yet.")
        else:
            bot.send_message(message.chat.id, f"📈 Last trade log:\n{lines[-1].strip()}")

@bot.message_handler(commands=['log'])
def trade_log(message):
    if not os.path.exists(TRADE_LOG_PATH):
        bot.send_message(message.chat.id, "No trade log yet.")
        return
    with open(TRADE_LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) > 1:
            bot.send_message(message.chat.id, f"🧾 Trade log (last closed):\n{lines[-1].strip()}")
        else:
            bot.send_message(message.chat.id, "No closed trades in log yet.")

@bot.message_handler(commands=['journal'])
def journal(message):
    if not os.path.exists(JOURNAL_PATH):
        bot.send_message(message.chat.id, "No journal entries yet.")
        return
    with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) > 1:
            bot.send_message(message.chat.id, f"📘 Journal (last):\n{lines[-1].strip()}")
        else:
            bot.send_message(message.chat.id, "No journal entries yet.")

@bot.message_handler(commands=["summary"])
def summary(message):
    from datetime import datetime

    if not os.path.exists(JOURNAL_PATH):
        bot.send_message(message.chat.id, "📄 No journal file found.")
        return

    try:
        df = pd.read_csv(JOURNAL_PATH, encoding="utf-8")
        if df.empty or "timestamp" not in df.columns:
            bot.send_message(message.chat.id, "📄 No trades in journal yet.")
            return

        # Parse timestamp and filter to today
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df.dropna(subset=["timestamp"], inplace=True)
        df["date"] = df["timestamp"].dt.strftime("%Y-%m-%d")
        today_str = datetime.now().strftime("%Y-%m-%d")

        today = df[df["date"] == today_str].copy()
        if today.empty:
            bot.send_message(message.chat.id, f"📊 No trades yet for {today_str}.")
            return

        # Closed trades only
        if "status" in today.columns:
            today = today[today["status"].astype(str).str.lower() == "closed"].copy()

        if today.empty:
            bot.send_message(message.chat.id, f"📊 No closed trades yet for {today_str}.")
            return

        # Ensure required columns
        for col in ["exit_reason", "pnl", "symbol"]:
            if col not in today.columns:
                raise ValueError(f"Missing '{col}' column in journal.csv")

        today["exit_reason"] = today["exit_reason"].astype(str)
        today["pnl"] = pd.to_numeric(today["pnl"], errors="coerce").fillna(0.0)

        # Bucket reasons using your existing helper
        buckets = today["exit_reason"].apply(_reason_buckets)
        tp3 = int((buckets == "tp3").sum())
        tp12 = int((buckets == "tp12").sum())
        sl = int((buckets == "sl").sum())
        other = int((buckets == "other").sum())

        total_trades = len(today)
        wins = tp3 + tp12
        losses = sl
        pnl_sum_pct = today["pnl"].sum()  # already percent

        # Mini TP/SL bar
        bar = _render_tp_sl_bar(tp3, tp12, sl, other, width=12)

        # Optional: list symbols that had TP3 today (top 3)
        tp3_syms = today.loc[(buckets == "tp3"), "symbol"].value_counts()
        tp3_syms_txt = ", ".join([f"{s}×{n}" for s, n in tp3_syms.head(3).items()]) if tp3 > 0 else "—"

        msg = (
            f"📊 Summary for {today_str}:\n"
            f"{bar}\n"
            f"🏁 Closed trades: {total_trades}\n"
            f"🏆 TP3: {tp3}  | 🎯 TP1–2: {tp12}  | 💥 SL: {sl}  | ❓ Other: {other}\n"
            f"✅ Wins: {wins}  | ❌ Losses: {losses}\n"
            f"📈 Total PnL: {pnl_sum_pct:.2f}%\n"
            f"🔎 TP3 symbols: {tp3_syms_txt}"
        )

        bot.send_message(message.chat.id, msg)

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Summary error: {e}")


def _reason_buckets(reason: str):
    """
    Normalize exit reasons into buckets for stats.
    Handles: 'TP3', 'TP1–2', 'TP1-2', 'TP1-Partial', 'SL', 'TrailingSL', etc.
    """
    r = (reason or "").upper().replace("–", "-")  # normalize en dash to hyphen
    if "TP3" in r:
        return "tp3"
    if "TP1-2" in r or "TP2" in r or "TP1-PARTIAL" in r or "TP1" in r:
        return "tp12"
    if r == "SL" or "STOP" in r:
        return "sl"
    return "other"

@bot.message_handler(commands=['journalstats'])
def handle_journal_stats(message):
    # Use JOURNAL as ground-truth, not ML log
    if not os.path.exists(JOURNAL_PATH):
        bot.reply_to(message, "No journal entries yet.")
        return

    try:
        df = pd.read_csv(JOURNAL_PATH, encoding="utf-8")
        if df.empty:
            bot.reply_to(message, "No journal entries yet.")
            return

        # Safety: fill missing
        for col in ["symbol", "exit_reason", "pnl"]:
            if col not in df.columns:
                raise ValueError(f"Missing '{col}' in journal.csv")
        df["symbol"] = df["symbol"].astype(str)
        df["exit_reason"] = df["exit_reason"].astype(str)
        df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0.0)

        # Closed trades only
        if "status" in df.columns:
            df = df[df["status"].astype(str).str.lower() == "closed"]

        # Aggregate by symbol
        response = "📘 TitanBot Journal Stats:\n"
        for symbol, sdf in df.groupby("symbol"):
            # Bucket exit reasons
            buckets = sdf["exit_reason"].apply(_reason_buckets)
            tp3 = (buckets == "tp3").sum()
            tp12 = (buckets == "tp12").sum()
            sl = (buckets == "sl").sum()
            other = (buckets == "other").sum()

            total = len(sdf)
            win = tp3 + tp12
            win_rate = (win / total) * 100 if total else 0.0

            avg_pnl = sdf["pnl"].mean()  # already in percent units

            response += (
                f"\n🔹 {symbol} ({total} trades)\n"
                f"  - 🏆 TP3: {tp3}\n"
                f"  - 🎯 TP1–2: {tp12}\n"
                f"  - 💥 SL: {sl}\n"
                f"  - ❓ Other: {other}\n"
                f"  - ✅ Win Rate: {win_rate:.1f}%\n"
                f"  - 💰 Avg PnL: {avg_pnl:.2f}%\n"
            )

        bot.reply_to(message, response or "No data.")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Stats error: {e}")

@bot.message_handler(commands=['rating'])
def handle_rating(message):
    # Last 50 from JOURNAL (ground truth)
    max_rows = 50
    if not os.path.exists(JOURNAL_PATH):
        bot.reply_to(message, "No journal entries yet.")
        return

    try:
        df = pd.read_csv(JOURNAL_PATH, encoding="utf-8")
        if "pnl" not in df.columns or "exit_reason" not in df.columns:
            raise ValueError("Missing 'pnl' or 'exit_reason' in journal.csv")

        # Closed trades only, last N
        if "status" in df.columns:
            df = df[df["status"].astype(str).str.lower() == "closed"]
        if df.empty:
            bot.reply_to(message, "No closed trades yet.")
            return

        rows = df.tail(max_rows).copy()
        rows["exit_reason"] = rows["exit_reason"].astype(str)

        counts = Counter()
        total_pnl = 0.0
        for _, row in rows.iterrows():
            bucket = _reason_buckets(row["exit_reason"])
            counts[bucket] += 1
            pnl_val = float(row.get("pnl", 0.0))
            total_pnl += pnl_val  # already percent

        total = counts["tp3"] + counts["tp12"] + counts["sl"] + counts["other"]
        win_total = counts["tp3"] + counts["tp12"]
        win_rate = (win_total / total) * 100 if total > 0 else 0.0

        response = (
            f"📊 TitanBot Stats (Last {total} Trades):\n"
            f"🏆 TP3 Wins: {counts['tp3']}\n"
            f"🎯 TP1–2 Wins: {counts['tp12']}\n"
            f"💥 SL Losses: {counts['sl']}\n"
            f"🤷 Other: {counts['other']}\n"
            f"✅ Win Rate: {win_rate:.1f}%\n"
            f"💰 Total PnL: {total_pnl:.2f}%"
        )
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Rating error: {e}")

def run_telegram_polling():
    bot.infinity_polling()

def send_startup_notice():
    bot.send_message(TELEGRAM_CHAT_ID, "🤖 TitanBot-Paper has started.\n" + COMMANDS_LIST)

def send_live_alert(message):
    bot.send_message(TELEGRAM_CHAT_ID, message)

def _render_tp_sl_bar(tp3:int, tp12:int, sl:int, other:int, width:int=12) -> str:
    """
    Renders a mini stacked bar (🟩 wins, 🟥 SL, ⬜ other) for today's closed trades.
    width = total blocks across all segments.
    """
    total = tp3 + tp12 + sl + other
    if total <= 0:
        return "—"

    win = tp3 + tp12
    # Proportional allocation across fixed width
    g = int(round(width * (win / total)))
    r = int(round(width * (sl / total)))
    # Ensure sum == width
    w = max(0, min(width, g))
    r = max(0, min(width - w, r))
    o = max(0, width - w - r)  # other remainder

    return "🟩" * w + "🟥" * r + "⬜" * o


if __name__ == "__main__":
    run_telegram_polling()
