# run_daily_universe.py (하루 1회 실행: watchlist 자동 생성)

from src.utils import ensure_dirs, load_config, log
from src.providers import USProvider, KoreaDailyProvider
from src.universe_sources import fetch_sp500_symbols, fetch_kospi200_symbols
from src.universe_builder import UniverseConfig, UniverseBuilder, save_watchlist

def main():
    cfg = load_config("config.yaml")
    ensure_dirs(cfg)

    us_symbols = fetch_sp500_symbols()
    kr_symbols = fetch_kospi200_symbols()  # pykrx 필요

    us_provider = USProvider()
    kr_provider = KoreaDailyProvider()

    uc = UniverseConfig(
        lookback_days=int(cfg["universe"]["lookback_days"]),
        dollar_vol_ma=int(cfg["universe"]["dollar_vol_ma"]),
        min_price_us=float(cfg["universe"]["min_price_us"]),
        min_dollar_vol_us=float(cfg["universe"]["min_dollar_vol_us"]),
        min_price_kr=float(cfg["universe"]["min_price_kr"]),
        min_value_traded_kr=float(cfg["universe"]["min_value_traded_kr"]),
        mom_w_126=float(cfg["universe"]["mom_w_126"]),
        mom_w_63=float(cfg["universe"]["mom_w_63"]),
        trend_ma=int(cfg["universe"]["trend_ma"]),
        use_50_200_filter=bool(cfg["universe"]["use_50_200_filter"]),
        top_n_us=int(cfg["universe"]["top_n_us"]),
        top_n_kr=int(cfg["universe"]["top_n_kr"]),
    )

    builder = UniverseBuilder(us_provider=us_provider, kr_provider=kr_provider)

    log(cfg, f"[DAILY] Fetch symbols: US(SP500)={len(us_symbols)}, KR(KOSPI200)={len(kr_symbols)}")

    us_list = builder.build_us(us_symbols, uc)
    save_watchlist(cfg["paths"]["watchlist_us"], us_list)
    log(cfg, f"[DAILY] US watchlist saved: {cfg['paths']['watchlist_us']} (n={len(us_list)})")

    if kr_symbols:
        kr_list = builder.build_kr(kr_symbols, uc)
        save_watchlist(cfg["paths"]["watchlist_kr"], kr_list)
        log(cfg, f"[DAILY] KR watchlist saved: {cfg['paths']['watchlist_kr']} (n={len(kr_list)})")
    else:
        log(cfg, "[DAILY] KR symbols empty (pykrx missing or failed).")

if __name__ == "__main__":
    main()
