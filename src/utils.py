import os
import json
import yaml
from datetime import datetime
import pytz

def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_dirs(cfg):
    data_dir = cfg["paths"]["data_dir"]
    os.makedirs(data_dir, exist_ok=True)

def now_str(cfg):
    tz = pytz.timezone(cfg["app"]["timezone"])
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def log(cfg, text: str):
    line = f"[{now_str(cfg)}] {text}\n"
    print(line, end="")
    with open(cfg["paths"]["log_file"], "a", encoding="utf-8") as f:
        f.write(line)

def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
