# ml/label_generator.py
import pandas as pd

def normalize_exit_reason(x: str) -> str:
    s = str(x or "").strip().lower()
    if s in {"tp3","tp_3","takeprofit3"}:
        return "TP3"
    if "tp" in s and "3" not in s:
        return "TP1–2"
    if "trailing" in s:
        return "TrailingSL"
    if s in {"sl","stop","stoploss","stop_loss"}:
        return "SL"
    return "Other"

def generate_labels(trade_df: pd.DataFrame) -> pd.DataFrame:
    """
    Accepts journal CLOSED trades; returns DataFrame with normalized exit_reason labels.
    """
    df = trade_df.copy()
    if "exit_reason" not in df.columns:
        df["exit_reason"] = "Other"
    df["exit_reason"] = df["exit_reason"].apply(normalize_exit_reason)
    return df
