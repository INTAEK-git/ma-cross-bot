from src.utils import ensure_dirs, load_config, log, load_json
from src.providers import USProvider
from src.notifier import TelegramNotifier
from src.trade_logic import evaluate_symbol
from src.signals import TradeConfig
from src.stores import PositionStore, StateStore

def main():
    cfg = load_config("config.yaml")
    ensure_dirs(cfg)

    # notifier에 logger 주입
    notifier_cfg = cfg["notifier"]["telegram"]
    notifier = TelegramNotifier(
        enabled=bool(notifier_cfg.get("enabled", True)),
        token_env=notifier_cfg.get("token_env", "TELEGRAM_BOT_TOKEN"),
        chat_id_env=notifier_cfg.get("chat_id_env", "TELEGRAM_CHAT_ID"),
        logger=lambda m: log(cfg, m),
    )

    # (선택) 실행될 때마다 “프로그램 살아있음” 로그 남기기
    log(cfg, "[INTRADAY] runner started")

    us_enabled = bool(cfg["intraday"]["market"]["us_enabled"])
    interval = cfg["intraday"]["interval"]
    lookback_days = int(cfg["intraday"]["lookback_days"])

    tcfg = TradeConfig(
        interval=interval,
        short_ma=int(cfg["strategy"]["short_ma"]),
        long_ma=int(cfg["strategy"]["long_ma"]),
        confirm_bars=int(cfg["strategy"]["confirm_bars"]),
        use_death_cross=bool(cfg["sell"]["use_death_cross"]),
        use_trailing_stop=bool(cfg["sell"]["use_trailing_stop"]),
        trailing_pct=float(cfg["sell"]["trailing_pct"]),
        use_atr_stop=bool(cfg["sell"]["use_atr_stop"]),
        atr_n=int(cfg["sell"]["atr_n"]),
        atr_k=float(cfg["sell"]["atr_k"]),
        use_time_stop=bool(cfg["sell"]["use_time_stop"]),
        max_hold_bars=int(cfg["sell"]["max_hold_bars"]),
    )

    pos_store = PositionStore(cfg["paths"]["positions"])
    state = StateStore(cfg["paths"]["state"])
    us_provider = USProvider()

    us_watch = load_json(cfg["paths"]["watchlist_us"], default=[])

    # watchlist 개수 로그
    log(cfg, f"[INTRADAY] watchlist_us size={len(us_watch)} interval={interval} lookback_days={lookback_days}")

    signals_sent = 0
    processed = 0

    if us_enabled:
        for item in us_watch:
            sym = item["symbol"]
            processed += 1

            df = us_provider.fetch_ohlcv(sym, interval=interval, lookback_days=lookback_days)
            if df is None or df.empty:
                log(cfg, f"[INTRADAY] {sym}: no data")
                continue

            key = f"US:{sym}"
            position = pos_store.get(key)
            action, reason, new_pos = evaluate_symbol(df, tcfg, position)

            bar_ts = str(df.index[-1])

            if action in ("BUY", "SELL"):
                last_alert = state.get_last_alert_ts(f"{key}:{action}")
                if last_alert == bar_ts:
                    log(cfg, f"[INTRADAY] {sym}: {action} duplicated on same bar -> skip")
                else:
                    price = float(df["Close"].iloc[-1])
                    msg = (
                        f"{'🟢 BUY' if action=='BUY' else '🔴 SELL'} (US)\n"
                        f"- Symbol: {sym}\n"
                        f"- Time: {bar_ts}\n"
                        f"- Price: {price:.2f}\n"
                        f"- Reason: {reason}\n"
                        f"- MA{tcfg.short_ma}/{tcfg.long_ma}, {tcfg.interval}\n"
                    )
                    ok = notifier.send(msg)
                    log(cfg, f"[INTRADAY] {sym}: action={action} reason={reason} telegram_ok={ok}")
                    state.set_last_alert_ts(f"{key}:{action}", bar_ts)
                    signals_sent += 1

            else:
                # 너무 시끄러우면 이 로그는 주석 처리해도 됨
                # log(cfg, f"[INTRADAY] {sym}: HOLD ({reason})")
                pass

            pos_store.set(key, new_pos)

    pos_store.save()
    state.save()

    log(cfg, f"[INTRADAY] runner finished processed={processed} signals_sent={signals_sent}")

    # ✅ 신호가 0개여도 “살아있음”을 텔레그램으로 받고 싶으면 아래 2줄 주석 해제
    # if signals_sent == 0:
    #     notifier.send("🟡 ma-cross-bot: 이번 실행에서 신호 없음(HOLD).")

if __name__ == "__main__":
    main()
