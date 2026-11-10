"""Instagram webhook serveri. Ishga tushirish: uvicorn app:app --host 0.0.0.0 --port 8000"""
import hashlib
import hmac
import json
import logging
import os
from collections import OrderedDict

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response

import agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ig-agent")

ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.getenv("IG_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("IG_APP_SECRET", "")
GRAPH = f"https://graph.instagram.com/{os.getenv('GRAPH_VERSION', 'v23.0')}"

app = FastAPI()
_seen: OrderedDict[str, None] = OrderedDict()  # takroriy webhooklarni o'tkazib yuborish uchun


def send_message(recipient_id: str, text: str):
    for i in range(0, len(text), 1000):  # Instagram bitta xabarda 1000 belgigacha ruxsat beradi
        r = httpx.post(
            f"{GRAPH}/me/messages",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            json={"recipient": {"id": recipient_id}, "message": {"text": text[i : i + 1000]}},
            timeout=30,
        )
        if r.status_code >= 400:
            log.error("Instagramga yuborishda xato %s: %s", r.status_code, r.text)
            return


def handle(sender_id: str, text: str):
    try:
        reply = agent.answer(sender_id, text)
    except Exception:
        log.exception("Javob tayyorlashda xato")
        reply = agent.FALLBACK
    send_message(sender_id, reply)


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
