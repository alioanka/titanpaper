# utils/terminal_logger.py
from datetime import datetime

def tlog(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open("terminal_log.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")
