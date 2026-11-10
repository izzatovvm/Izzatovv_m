"""Instagram API (Unified login) bilan ishlash: akkauntni aniqlash, suhbatlarni o'qish, xabar yuborish."""
import logging
import os
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("ig-agent")

ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
GRAPH = f"https://graph.facebook.com/{os.getenv('GRAPH_VERSION', 'v26.0')}"
_http = httpx.Client(timeout=30, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
_ig_id = os.getenv("IG_USER_ID", "")


def ig_id() -> str:
    """Token ulangan Instagram akkauntining ID raqami."""
    global _ig_id
    if not _ig_id:
        r = _http.get(f"{GRAPH}/me/assigned_instagram_accounts")
        r.raise_for_status()
        _ig_id = r.json()["data"][0]["id"]
    return _ig_id


def parse_time(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")


def recent_conversations(limit: int = 10, messages: int = 8) -> list[dict]:
    """Oxirgi suhbatlar; har birida eng yangi xabarlar (yangisi birinchi)."""
    r = _http.get(
        f"{GRAPH}/{ig_id()}/conversations",
        params={
            "platform": "instagram",
            "limit": limit,
            "fields": f"updated_time,messages.limit({messages}){{id,created_time,from,message}}",
        },
    )
    r.raise_for_status()
    return r.json().get("data", [])


def send_message(recipient_id: str, text: str) -> bool:
    for i in range(0, len(text), 1000):  # Instagram bitta xabarda 1000 belgigacha ruxsat beradi
        r = _http.post(
            f"{GRAPH}/{ig_id()}/messages",
            json={"recipient": {"id": recipient_id}, "message": {"text": text[i : i + 1000]}},
        )
        if r.status_code >= 400:
            log.error("Instagramga yuborishda xato %s: %s", r.status_code, r.text)
            return False
    return True
