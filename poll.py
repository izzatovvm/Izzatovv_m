"""Agentni ishga tushirish: python poll.py

Har POLL_SECONDS soniyada Instagram direktini tekshiradi va ishga tushgandan KEYIN kelgan
yangi xabarlarga javob beradi. Eski xabarlarga tegmaydi. Server yoki webhook kerak emas.
GitHub Actions uchun: RUN_MINUTES=4 (shuncha daqiqa ishlab to'xtaydi) va LOOKBACK_MINUTES=45
(oxirgi 45 daqiqada kelib, hali javobsiz qolgan xabarlarga ham javob beradi).
Akkaunt egasi suhbatga o'zi yozsa, agent o'sha suhbatda MANUAL_PAUSE_MINUTES daqiqa jim turadi.
DRY_RUN=1 bo'lsa hech narsa yubormaydi, faqat nima qilishini ko'rsatadi."""
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import agent
import ig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("ig-agent")

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))
RUN_MINUTES = float(os.getenv("RUN_MINUTES", "0"))  # 0 = to'xtamasdan ishlaydi
LOOKBACK_MINUTES = float(os.getenv("LOOKBACK_MINUTES", "0"))
# Egasi o'zi yozgan suhbatda agent shuncha daqiqa aralashmaydi
MANUAL_PAUSE_MINUTES = float(os.getenv("MANUAL_PAUSE_MINUTES", "30"))
DRY_RUN = os.getenv("DRY_RUN") == "1"
# Vergul bilan ajratilgan usernamelar; berilsa, faqat shularga javob beradi (sinov uchun)
ONLY = {u.strip().lower() for u in os.getenv("ONLY_USERNAMES", "").split(",") if u.strip()}


def owner_active(msgs: list[dict], me: str, sent: set[str]) -> bool:
    """Akkaunt egasi shu suhbatga yaqinda o'zi (agent emas) yozganmi?"""
    since = datetime.now(timezone.utc) - timedelta(minutes=MANUAL_PAUSE_MINUTES)
    for m in msgs:
        if (m.get("from") or {}).get("id") != me or ig.parse_time(m["created_time"]) < since:
            continue
        if m["id"] not in sent and ig.MARK not in (m.get("message") or ""):
            return True
    return False


def check(start: datetime, done: set[str], sent: set[str]):
    me = ig.ig_id()
    for conv in ig.recent_conversations():
        msgs = (conv.get("messages") or {}).get("data") or []
        if not msgs:
            continue
        last = msgs[0]
        sender = last.get("from") or {}
        if sender.get("id") == me or last["id"] in done or ig.parse_time(last["created_time"]) < start:
            continue  # o'zimizning xabar, javob berilgan yoki eski xabar
        username = sender.get("username", "?")
        if ONLY and username.lower() not in ONLY:
            continue
        done.add(last["id"])
        if owner_active(msgs, me, sent):
            log.info("@%s: egasi o'zi yozishyapti, agent aralashmaydi", username)
            continue
        text = (last.get("message") or "").strip()
        if not text:
            continue  # rasm, ovozli xabar va h.k.
        history = [
            {"role": "model" if (m.get("from") or {}).get("id") == me else "user",
             "parts": [{"text": m["message"]}]}
            for m in reversed(msgs[1:]) if m.get("message")
        ]
        while history and history[0]["role"] != "user":  # Gemini tarixi "user"dan boshlanishi kerak
            history.pop(0)
        try:
            reply = agent.answer(sender["id"], text, history=history)
        except Exception:
            log.exception("Javob tayyorlashda xato (@%s)", username)
            done.discard(last["id"])  # keyingi tekshiruvda qayta urinadi
            continue
        if DRY_RUN:
            log.info("[DRY_RUN] @%s ga javob yuborilmadi: %s", username, reply)
        else:
            ids = ig.send_message(sender["id"], reply)
            if ids is not None:
                sent.update(ids)
                log.info("@%s ga javob berildi", username)


def main():
    began = time.monotonic()
    start = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    done: set[str] = set()
    sent: set[str] = set()  # shu ishga tushishda agent yuborgan xabarlar
    log.info("Agent ishga tushdi. Har %s soniyada tekshiradi.%s", POLL_SECONDS, " DRY_RUN" if DRY_RUN else "")
    while True:
        try:
            check(start, done, sent)
        except ig.Blocked as e:
            log.error("Meta ilovaning API'ga kirishini to'sib qo'ygan, agent to'xtadi: %s", e)
            sys.exit(1)
        except Exception:
            log.exception("Tekshirishda xato")
        if RUN_MINUTES and time.monotonic() - began + POLL_SECONDS > RUN_MINUTES * 60:
            break
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
