"""Bilimlar bazasi: knowledge/ papkasidagi .md/.txt fayllarni o'qiydi,
bo'laklarga ajratadi va savolga eng mos bo'laklarni topadi."""
import hashlib
import os
import json
import math
import threading
import time
from pathlib import Path

CHUNK_SIZE = 900  # bitta bo'lakning taxminiy uzunligi (belgi)


def _chunks(text: str) -> list[str]:
    out, cur = [], ""
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        if cur and len(cur) + len(para) > CHUNK_SIZE:
            out.append(cur)
            cur = ""
        cur = f"{cur}\n\n{para}" if cur else para
        while len(cur) > CHUNK_SIZE * 2:  # juda uzun abzats
            out.append(cur[: CHUNK_SIZE * 2])
            cur = cur[CHUNK_SIZE * 2 :]
    if cur:
        out.append(cur)
    return out


def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / ((math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))) or 1)


class KnowledgeBase:
    def __init__(self, client, folder="knowledge", embed_model="gemini-embedding-001",
                 cache_path=".kb_cache.json"):
        self.client = client
        self.folder = Path(folder)
        self.embed_model = embed_model
        self.cache_path = Path(cache_path)
        self.items: list[tuple[str, list[float]]] = []
        self._stamp = None
        self._lock = threading.Lock()

    def _files(self):
        return sorted(p for p in self.folder.rglob("*") if p.suffix.lower() in (".md", ".txt"))

    def _current_stamp(self):
        return tuple((str(p), p.stat().st_mtime_ns) for p in self._files()) + (os.getenv("PRIVATE_KNOWLEDGE", ""),)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        res = []
        for i in range(0, len(texts), 50):
            for attempt in range(3):  # server band bo'lsa qayta urinamiz
                try:
                    r = self.client.models.embed_content(model=self.embed_model, contents=texts[i : i + 50])
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(2 * (attempt + 1))
            res += [e.values for e in r.embeddings]
        return res

    def refresh(self):
        """Fayllar o'zgargan bo'lsa bazani qayta yuklaydi (qayta ishga tushirish shart emas)."""
        with self._lock:
            stamp = self._current_stamp()
            if stamp == self._stamp:
                return
            cache = {}
            if self.cache_path.exists():
                try:
                    cache = json.loads(self.cache_path.read_text())
                except ValueError:
                    cache = {}
            texts = []
            for p in self._files():
                for c in _chunks(p.read_text(encoding="utf-8")):
                    texts.append(f"[{p.name}]\n{c}")
            # Maxfiy ma'lumot (masalan telefon raqam) faylda emas, PRIVATE_KNOWLEDGE o'zgaruvchisida turadi
            for c in _chunks(os.getenv("PRIVATE_KNOWLEDGE", "").replace("\\n", "\n")):
                texts.append(f"[maxfiy]\n{c}")
            keys = [hashlib.sha256(f"{self.embed_model}:{t}".encode()).hexdigest() for t in texts]
            missing = [(k, t) for k, t in zip(keys, texts) if k not in cache]
            if missing:
                for (k, _), v in zip(missing, self._embed([t for _, t in missing])):
                    cache[k] = v
            self.items = [(t, cache[k]) for k, t in zip(keys, texts)]
            self.cache_path.write_text(json.dumps({k: cache[k] for k in keys}))
            self._stamp = stamp

    def search(self, query: str, k: int = 5) -> list[str]:
        self.refresh()
        if not self.items:
            return []
        q = self._embed([query])[0]
        ranked = sorted(self.items, key=lambda it: _cos(q, it[1]), reverse=True)
        return [t for t, _ in ranked[:k]]
