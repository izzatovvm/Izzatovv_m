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
        _check(r)
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
    _check(r)
    return r.json().get("data", [])


# Agent yuborgan xabarlarga qo'shiladigan ko'rinmas belgi: shu orqali agent o'z xabarini
# akkaunt egasi qo'lda yozgan xabardan ajratadi.
MARK = "\u200b"


class Blocked(Exception):
    """Meta ilovaning API'ga kirishini to'sib qo'ygan."""


def _check(r: httpx.Response):
    if r.status_code >= 400:
        if "API access blocked" in r.text:
            raise Blocked(r.text)
        r.raise_for_status()


def mark(text: str) -> str:
    head, sep, tail = text.partition(" ")
    return f"{head}{MARK}{sep}{tail}"


def send_message(recipient_id: str, text: str) -> list[str] | None:
    """Yuborilgan xabarlarning ID ro'yxatini qaytaradi; xato bo'lsa None."""
    ids = []
    text = mark(text)
    for i in range(0, len(text), 1000):  # Instagram bitta xabarda 1000 belgigacha ruxsat beradi
        r = _http.post(
            f"{GRAPH}/{ig_id()}/messages",
            json={"recipient": {"id": recipient_id}, "message": {"text": text[i : i + 1000]}},
        )
        if r.status_code >= 400:
            log.error("Instagramga yuborishda xato %s: %s", r.status_code, r.text)
            return None
        ids.append(r.json().get("message_id", ""))
    return ids
