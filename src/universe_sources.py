import pandas as pd
import requests
def fetch_sp500_symbols():
    """
    Wikipedia의 S&P500 구성종목 표를 자동 파싱
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()

    # read_html은 "URL" 대신 "HTML 문자열"도 받을 수 있음
    tables = pd.read_html(r.text)
    df = tables[0]  # 첫 테이블이 보통 S&P500 구성표
    return df["Symbol"].tolist()

def fetch_kospi200_symbols():
    """
    pykrx로 KOSPI200 구성종목 티커(6자리) 수집
    """
    try:
        from pykrx import stock
    except Exception:
        return []
    try:
        # KOSPI200 티커 리스트
        # pykrx 버전에 따라 함수가 다를 수 있어 방어적으로 처리
        # 가장 흔한: stock.get_index_portfolio_deposit_file("1028") (KOSPI200 지수코드)
        tickers = stock.get_index_portfolio_deposit_file("1028")
        # tickers: ['005930', ...]
        return list(tickers)
    except Exception:
        return []
