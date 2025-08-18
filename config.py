# config.py
import os

# ========== General ==========
BOT_NAME = "TitanBot-Paper"
BASE_CURRENCY = "USDT"
EXCHANGE = "binance"
MODE = "paper"

# Symbols you want to track
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# ========== Paths ==========
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Ensure canonical relative paths (writers will create dir lazily)
TRADE_LOG_PATH = os.path.join(LOG_DIR, "trade_log.csv")
JOURNAL_PATH    = os.path.join(LOG_DIR, "journal.csv")
BALANCE_LOG_PATH = os.path.join(LOG_DIR, "balance_history.csv")

# ML log stays in project root (do NOT move)
ML_LOG_FILE = "ml_log.csv"

# ========== Telegram ==========
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")   # set in .env
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "") # set in .env

# ========== Engine / Risk ==========
INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "5000"))

# Timeframe and loop interval
TIMEFRAME = os.getenv("TIMEFRAME", "5m")         # more trades: "3m"
EVALUATION_INTERVAL = int(os.getenv("EVAL_SECS", "60"))

# Entry filters — loosen carefully to increase trade count
MIN_TREND_STRENGTH = float(os.getenv("MIN_TREND_STRENGTH", "0.0008"))  # 0.08%
MIN_VOLATILITY     = float(os.getenv("MIN_VOLATILITY", "0.0009"))      # 0.09%

# Cooldown per symbol after a close (seconds)
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "600"))

# ========== TP/SL ==========
# True Range derived stops/targets (multipliers of ATR)
TP_MULTIPLIERS = [3.0, 5.0, 8.0]
SL_MULTIPLIER  = 1.5

# Start trailing only AFTER which TP index? (2 => after TP2)
TRAILING_START_AFTER_TP = 2

# Trailing gap in ATR units (wider = less premature stopouts)
TRAILING_GAP_ATR = 1.1

# Price buffer to avoid wick noise (0.02% default)
PRICE_BUFFER_PCT = float(os.getenv("PRICE_BUFFER_PCT", "0.0002"))

# ========== Misc ==========
# Max expected duration in seconds before forcing close (optional; set 0 to disable)
MAX_TRADE_DURATION_SEC = int(os.getenv("MAX_TRADE_DURATION_SEC", "0"))

# Writers create dirs lazily; nothing to pre-create here.
