from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import json
import numpy as np
import pandas as pd

def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()

def ret_n(s: pd.Series, n: int) -> float:
    if len(s) <= n:
        return np.nan
    return float(s.iloc[-1] / s.iloc[-1 - n] - 1.0)

@dataclass
class UniverseConfig:
    lookback_days: int = 365
    top_n_us: int = 80
    top_n_kr: int = 80

    dollar_vol_ma: int = 20

    # US 유동성
    min_price_us: float = 5.0
    min_dollar_vol_us: float = 5e7  # $50M/day

    # KR 유동성 (거래대금 대신 Close*Volume로 근사)
    min_price_kr: float = 1000.0
    min_value_traded_kr: float = 2e10  # 200억/일

    # 모멘텀 가중치
    mom_w_126: float = 0.6
    mom_w_63: float = 0.4

    # 추세
    trend_ma: int = 200
    use_50_200_filter: bool = True

class UniverseBuilder:
    def __init__(self, us_provider, kr_provider):
        self.us_provider = us_provider
        self.kr_provider = kr_provider

    def build_us(self, symbols: List[str], cfg: UniverseConfig) -> List[Dict]:
        rows = []
        for sym in symbols:
            df = self.us_provider.fetch_ohlcv(sym, interval="1d", lookback_days=cfg.lookback_days)
            if df is None or df.empty or len(df) < cfg.trend_ma + 60:
                continue

            c = df["Close"].astype(float)
            v = df["Volume"].astype(float)

            price = float(c.iloc[-1])
            if price < cfg.min_price_us:
                continue

            dollar_vol = (c * v).rolling(cfg.dollar_vol_ma, min_periods=cfg.dollar_vol_ma).mean()
            dv = float(dollar_vol.iloc[-1]) if len(dollar_vol) else 0.0
            if dv < cfg.min_dollar_vol_us:
                continue

            ma200 = sma(c, cfg.trend_ma)
            if np.isnan(ma200.iloc[-1]) or not (c.iloc[-1] > ma200.iloc[-1]):
                continue

            if cfg.use_50_200_filter:
                ma50 = sma(c, 50)
                if np.isnan(ma50.iloc[-1]) or not (ma50.iloc[-1] > ma200.iloc[-1]):
                    continue

            r126 = ret_n(c, 126)
            r63 = ret_n(c, 63)
            if np.isnan(r126) or np.isnan(r63):
                continue

            score = cfg.mom_w_126 * r126 + cfg.mom_w_63 * r63

            rows.append({
                "symbol": sym,
                "price": price,
                "liquidity": dv,
                "ret_126": r126,
                "ret_63": r63,
                "score": score,
                "source": "SP500",
            })

        if not rows:
            return []
        out = pd.DataFrame(rows).sort_values(["score", "liquidity"], ascending=[False, False]).head(cfg.top_n_us)
        return out.to_dict(orient="records")

    def build_kr(self, symbols: List[str], cfg: UniverseConfig) -> List[Dict]:
        rows = []
        for sym in symbols:
            df = self.kr_provider.fetch_ohlcv(sym, interval="1d", lookback_days=cfg.lookback_days)
            if df is None or df.empty or len(df) < cfg.trend_ma + 60:
                continue

            c = df["Close"].astype(float)
            v = df["Volume"].astype(float)

            price = float(c.iloc[-1])
            if price < cfg.min_price_kr:
                continue

            # KR 유동성: 거래대금이 없으니 Close*Volume로 근사
            value_traded = (c * v).rolling(cfg.dollar_vol_ma, min_periods=cfg.dollar_vol_ma).mean()
            vt = float(value_traded.iloc[-1]) if len(value_traded) else 0.0
            if vt < cfg.min_value_traded_kr:
                continue

            ma200 = sma(c, cfg.trend_ma)
            if np.isnan(ma200.iloc[-1]) or not (c.iloc[-1] > ma200.iloc[-1]):
                continue

            if cfg.use_50_200_filter:
                ma50 = sma(c, 50)
                if np.isnan(ma50.iloc[-1]) or not (ma50.iloc[-1] > ma200.iloc[-1]):
                    continue

            r126 = ret_n(c, 126)
            r63 = ret_n(c, 63)
            if np.isnan(r126) or np.isnan(r63):
                continue

            score = cfg.mom_w_126 * r126 + cfg.mom_w_63 * r63

            rows.append({
                "symbol": sym,
                "price": price,
                "liquidity": vt,
                "ret_126": r126,
                "ret_63": r63,
                "score": score,
                "source": "KOSPI200",
            })

        if not rows:
            return []
        out = pd.DataFrame(rows).sort_values(["score", "liquidity"], ascending=[False, False]).head(cfg.top_n_kr)
        return out.to_dict(orient="records")

def save_watchlist(path: str, items: List[Dict]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
