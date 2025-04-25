# utils
# Cherry_C9H13N created on 2025/4/25
from datetime import datetime, timedelta, timezone


def format_timestamp(ts):
    tz = timezone(timedelta(hours=8))
    return datetime.fromtimestamp(ts, tz).strftime("%Y-%m-%d  %H:%M:%S")


def new_folder_name(existing_names):
    import re
    pattern = re.compile(r"^存档(\d+)$")
    max_n = 0
    for name in existing_names:
        match = pattern.match(name)
        if match:
            n = int(match.group(1))
            if n > max_n:
                max_n = n
    return f"存档{max_n + 1}"
