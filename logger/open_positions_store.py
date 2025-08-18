# logger/open_positions_store.py
# New file: JSON-backed store for open trades. Atomic writes; fail-closed.

import os, json, tempfile
from typing import List, Dict, Optional
from config import LOG_DIR

STORE_PATH = os.path.join(LOG_DIR, "open_positions.json")

def _ensure_dir():
    os.makedirs(LOG_DIR, exist_ok=True)

def load_open_positions() -> List[Dict]:
    _ensure_dir()
    if not os.path.exists(STORE_PATH) or os.path.getsize(STORE_PATH) == 0:
        return []
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_open_positions(positions: List[Dict]):
    _ensure_dir()
    tmp = STORE_PATH + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(positions, f, ensure_ascii=False)
        os.replace(tmp, STORE_PATH)
    except Exception as e:
        # fail-closed: do nothing but avoid crashing trading loop
        print(f"⚠️ save_open_positions error: {e}")

def upsert_position(pos: Dict, positions: Optional[List[Dict]] = None) -> List[Dict]:
    if positions is None:
        positions = load_open_positions()
    tid = str(pos.get("trade_id",""))
    out = []
    found = False
    for p in positions:
        if str(p.get("trade_id","")) == tid and tid:
            out.append(pos); found = True
        else:
            out.append(p)
    if not found:
        out.append(pos)
    save_open_positions(out)
    return out

def remove_position(trade_id: str, positions: Optional[List[Dict]] = None) -> List[Dict]:
    if positions is None:
        positions = load_open_positions()
    out = [p for p in positions if str(p.get("trade_id","")) != str(trade_id)]
    save_open_positions(out)
    return out
