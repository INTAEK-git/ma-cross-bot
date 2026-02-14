from __future__ import annotations
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from .signals import TradeConfig, cross_up, cross_down, atr

def evaluate_symbol(df: pd.DataFrame, cfg: TradeConfig, position: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    if df is None or df.empty:
        return "HOLD", "no_data", position

    last_close = float(df["Close"].iloc[-1])
    last_ts = str(df.index[-1])

    in_pos = bool(position.get("in_position", False))

    # BUY
    if not in_pos:
        if cross_up(df, cfg):
            new_pos = {
                "in_position": True,
                "entry_price": last_close,
                "entry_ts": last_ts,
                "peak_price": last_close,
                "bars_held": 0,
            }
            return "BUY", "golden_cross", new_pos
        return "HOLD", "no_buy", position

    # update stats
    peak = float(position.get("peak_price", last_close))
    peak = max(peak, last_close)
    bars_held = int(position.get("bars_held", 0)) + 1

    triggers = []

    if cfg.use_death_cross and cross_down(df, cfg):
        triggers.append("death_cross")

    if cfg.use_trailing_stop:
        if last_close <= peak * (1.0 - cfg.trailing_pct):
            triggers.append(f"trailing_stop({cfg.trailing_pct*100:.1f}%)")

    if cfg.use_atr_stop:
        a = atr(df, cfg.atr_n)
        if a is not None and not a.empty and not np.isnan(a.iloc[-1]):
            stop_price = float(position["entry_price"]) - cfg.atr_k * float(a.iloc[-1])
            if last_close <= stop_price:
                triggers.append(f"atr_stop(k={cfg.atr_k})")

    if cfg.use_time_stop and bars_held >= cfg.max_hold_bars:
        triggers.append(f"time_stop({cfg.max_hold_bars} bars)")

    if triggers:
        return "SELL", " & ".join(triggers), {"in_position": False}

    position["peak_price"] = peak
    position["bars_held"] = bars_held
    return "HOLD", "in_position", position
