"""Ixtiyoriy: webhook serveri (poll.py o'rniga, ochiq HTTPS manzilingiz bo'lsa). Ishga tushirish: uvicorn app:app --host 0.0.0.0 --port 8000"""
import hashlib
import hmac
import json
import logging
import os
from collections import OrderedDict

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response

import agent
import ig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ig-agent")

VERIFY_TOKEN = os.getenv("IG_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("IG_APP_SECRET", "")

app = FastAPI()
_seen: OrderedDict[str, None] = OrderedDict()  # takroriy webhooklarni o'tkazib yuborish uchun


def handle(sender_id: str, text: str):
    try:
        reply = agent.answer(sender_id, text)
    except Exception:
        log.exception("Javob tayyorlashda xato")
        reply = agent.FALLBACK
    ig.send_message(sender_id, reply)


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/webhook")
def verify(request: Request):
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and VERIFY_TOKEN and q.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(q.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(403)


@app.post("/webhook")
async def webhook(request: Request, tasks: BackgroundTasks):
    body = await request.body()
    if APP_SECRET:
        expected = "sha256=" + hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, request.headers.get("x-hub-signature-256", "")):
            raise HTTPException(403)
    data = json.loads(body or b"{}")
    for entry in data.get("entry", []):
        for ev in entry.get("messaging", []):
            msg = ev.get("message") or {}
            text, mid = msg.get("text"), msg.get("mid")
            if msg.get("is_echo") or not text or not mid or mid in _seen:
                continue  # o'zimiz yuborgan, matnsiz yoki takroriy xabar
            _seen[mid] = None
            if len(_seen) > 5000:
                _seen.popitem(last=False)
            tasks.add_task(handle, ev["sender"]["id"], text)
    return {"ok": True}
