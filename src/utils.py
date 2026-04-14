import os
import re
from datetime import datetime, timezone
from dateutil import parser as dtparser

def debug_log(msg: str):
    """
    DEBUG 환경 변수가 '1'일 때만 메세지를 출력합니다.
    """
    if os.environ.get("DEBUG") == "1":
        print(f"[DEBUG] {msg}")

def slugify_case_name(name: str) -> str:
    """
    Case name을 URL에 적합한 slug 형태로 변환합니다.
    """
    name = (name or "").lower()
    name = name.replace("v.", "v")
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")

def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = dtparser.parse(s)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None
