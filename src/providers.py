from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import yfinance as yf

@dataclass
class USProvider:
    @staticmethod
    def yahoo_symbol(sym: str) -> str:
        return sym.replace(".", "-").replace("$", "")

    def fetch_ohlcv(self, symbol: str, interval: str, lookback_days: int) -> pd.DataFrame:
        period = f"{lookback_days}d"
        safe_symbol = self.yahoo_symbol(symbol)
        df = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if df is None or df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        need = ["Open", "High", "Low", "Close", "Volume"]
        cols = [c for c in need if c in df.columns]
        out = df[cols].copy()
        out.dropna(inplace=True)
        return out

@dataclass
class KoreaDailyProvider:
    """
    KOSPI200 자동 수집 + 일봉 데이터(모멘텀/추세/유동성 필터용)
    - 증권사 API 없이 pykrx로 처리
    """
    def fetch_ohlcv(self, symbol: str, interval: str, lookback_days: int) -> pd.DataFrame:
        if interval != "1d":
            # 5분봉은 향후 API 붙일 자리
            return pd.DataFrame()

        try:
            from pykrx import stock
        except Exception:
            return pd.DataFrame()

        # symbol: 6자리 티커(예: "005930")
        # pykrx는 날짜 문자열이 필요
        import datetime
        end = datetime.datetime.now().strftime("%Y%m%d")
        start = (datetime.datetime.now() - datetime.timedelta(days=lookback_days)).strftime("%Y%m%d")

        df = stock.get_market_ohlcv_by_date(start, end, symbol)
        if df is None or df.empty:
            return pd.DataFrame()

        # 컬럼 표준화
        # pykrx: 시가/고가/저가/종가/거래량/거래대금
        mapping = {"시가":"Open","고가":"High","저가":"Low","종가":"Close","거래량":"Volume"}
        df = df.rename(columns=mapping)
        keep = ["Open","High","Low","Close","Volume"]
        df = df[[c for c in keep if c in df.columns]].copy()
        df.index = pd.to_datetime(df.index)
        df.dropna(inplace=True)
        return df
