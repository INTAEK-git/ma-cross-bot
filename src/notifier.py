import os
import requests
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class TelegramNotifier:
    token_env: str
    chat_id_env: str
    enabled: bool = True
    logger: Optional[Callable[[str], None]] = None  # log(msg) 같은 함수 주입

    def _log(self, msg: str):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    def _get_creds(self):
        token = os.getenv(self.token_env, "")
        chat_id = os.getenv(self.chat_id_env, "")
        return token, chat_id

    def send(self, text: str) -> bool:
        if not self.enabled:
            self._log("[TG] disabled -> skip")
            return False

        token, chat_id = self._get_creds()
        if not token or not chat_id:
            self._log(f"[TG] env missing -> token({self.token_env})={'Y' if token else 'N'}, chat_id({self.chat_id_env})={'Y' if chat_id else 'N'}")
            self._log("[TG] message skipped. (Set env vars and reopen terminal)")
            return False

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code != 200:
                self._log(f"[TG] send failed: {r.status_code} {r.text}")
                return False
            self._log("[TG] send ok")
            return True
        except Exception as e:
            self._log(f"[TG] exception: {e}")
            return False

    def test(self) -> bool:
        return self.send("✅ ma-cross-bot 텔레그램 테스트 메시지입니다.")
