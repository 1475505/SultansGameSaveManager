# config
# Cherry_C9H13N created on 2025/4/25
import json
import os
from constants import CONFIG_FILE, SETTING_FILE, DEFAULT_PATH


def load_setting():
    if not os.path.exists(SETTING_FILE):
        return {}
    with open(SETTING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_setting(setting_dict):
    with open(SETTING_FILE, "w", encoding="utf-8") as f:
        json.dump(setting_dict, f, ensure_ascii=False, indent=2)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return []
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
