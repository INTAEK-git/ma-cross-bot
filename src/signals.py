from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import numpy as np

def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1
    ).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()

@dataclass
class TradeConfig:
    interval: str = "5m"
    short_ma: int = 20
    long_ma: int = 60
    confirm_bars: int = 1

    use_death_cross: bool = True
    use_trailing_stop: bool = True
    trailing_pct: float = 0.03

    use_atr_stop: bool = True
    atr_n: int = 14
    atr_k: float = 2.5

    use_time_stop: bool = False
    max_hold_bars: int = 72

def cross_up(df: pd.DataFrame, cfg: TradeConfig) -> bool:
    if df.empty or len(df) < cfg.long_ma + cfg.confirm_bars + 2:
        return False
    d = df.copy()
    d["ma_s"] = sma(d["Close"], cfg.short_ma)
    d["ma_l"] = sma(d["Close"], cfg.long_ma)
    d.dropna(inplace=True)
    if len(d) < cfg.confirm_bars + 2:
        return False

    tail = d.iloc[-cfg.confirm_bars:]
    if not (tail["ma_s"] > tail["ma_l"]).all():
        return False

    prev = d.iloc[-cfg.confirm_bars - 1]
    return bool(prev["ma_s"] <= prev["ma_l"])

def cross_down(df: pd.DataFrame, cfg: TradeConfig) -> bool:
    if df.empty or len(df) < cfg.long_ma + cfg.confirm_bars + 2:
        return False
    d = df.copy()
    d["ma_s"] = sma(d["Close"], cfg.short_ma)
    d["ma_l"] = sma(d["Close"], cfg.long_ma)
    d.dropna(inplace=True)
    if len(d) < cfg.confirm_bars + 2:
        return False

    tail = d.iloc[-cfg.confirm_bars:]
    if not (tail["ma_s"] < tail["ma_l"]).all():
        return False

    prev = d.iloc[-cfg.confirm_bars - 1]
    return bool(prev["ma_s"] >= prev["ma_l"])
