import json
from pathlib import Path
from typing import Dict, Any

class PositionStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.pos: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.pos = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.pos = {}
        else:
            self.pos = {}

    def save(self):
        self.path.write_text(json.dumps(self.pos, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str) -> Dict[str, Any]:
        return self.pos.get(key, {"in_position": False})

    def set(self, key: str, data: Dict[str, Any]):
        self.pos[key] = data

class StateStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.state: Dict[str, Any] = {}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.state = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.state = {}
        else:
            self.state = {}

    def save(self):
        self.path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_last_alert_ts(self, key: str):
        return self.state.get(key)

    def set_last_alert_ts(self, key: str, ts: str):
        self.state[key] = ts
