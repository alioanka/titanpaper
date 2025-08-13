# config.py
import os

### === GENERAL SETTINGS === ###
BOT_NAME = "TitanBot-Paper"
BASE_CURRENCY = "USDT"
EXCHANGE = "binance"
MODE = "paper"

### === SYMBOLS TO TRACK === ###
SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT"
]

### === STRATEGY SETTINGS === ###
TIMEFRAME = "5m"  # Binance supported intervals: 1m, 3m, 5m, 15m, etc.
MIN_TREND_STRENGTH = 0.0001
MIN_VOLATILITY = 0.0003  # % per candle

### === PAPER TRADING CONFIG === ###
INITIAL_BALANCE = 5000.0
MAX_RISK_PER_TRADE = 0.02  # 2% of balance
TP_MULTIPLIERS = [6, 9, 14]
SL_MULTIPLIER = 4
MIN_SPREAD_PCT = 0.002  # 0.2%
#TRAILING_START_AFTER_TP = 1  # After TP1, activate trailing
#TRAILING_GAP_ATR = 0.5
RISK_PER_TRADE = 0.02  # 2% of total balance per trade


### === LOGGING === ###
#TRADE_LOG_PATH = "logs/trade_log.csv"
#JOURNAL_PATH = "logs/journal.csv"
#BALANCE_LOG_PATH = "logs/balance_history.csv"

# Telegram Bot Config
TELEGRAM_TOKEN = "7678357905:AAEe0MfHa4ZYhFnDhlUPL2oDaNXSoLo-YaM"
TELEGRAM_CHAT_ID = "462007586"

EVALUATION_INTERVAL = 30
DEFAULT_STRATEGY_NAME = "SmartTrendStrategy"

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
# =========================
# 📂 Logging & Data Paths
# =========================
import os as _os

# Project root and logs dir
_BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
LOG_DIR = _os.path.join(_BASE_DIR, "logs")
_os.makedirs(LOG_DIR, exist_ok=True)

# File paths used across the project
BALANCE_LOG_PATH = _os.path.join(LOG_DIR, "balance_history.csv")
TRADE_LOG_PATH   = _os.path.join(LOG_DIR, "trade_log.csv")
JOURNAL_PATH     = _os.path.join(LOG_DIR, "journal.csv")

# ⚠️ IMPORTANT: ML log stays in project root to match utils/ml_logger.py (ML_LOG_FILE = "ml_log.csv")
# Do NOT move it to LOG_DIR unless you also change utils/ml_logger.py.

# Ensure CSVs are created lazily by their writers (no eager create here).

# =========================
# 🧭 Strategy Tweaks (safer TP3 capture in bull runs)
# =========================
# Start trailing only AFTER TP2 has hit (prevents cutting big trends early)
TRAILING_START_AFTER_TP = 2

# Widen trailing gap a bit (was likely too tight)
# Typical range: 1.0–1.3 ATR for 5m trend-following
TRAILING_GAP_ATR = 1.1

# (Optional) If TP3 is rarely reached, consider slightly nearer targets:
# TP_MULTIPLIERS = [2.5, 4.0, 6.5]  # <= uncomment only if you want closer TP3
