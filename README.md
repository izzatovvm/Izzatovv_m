# Instagram AI agent

Instagram direktiga yozgan do'stlar va yaqinlarga siz band bo'lganingizda Google Gemini API orqali javob beradigan shaxsiy AI yordamchi. Oddiy suhbatni o'zi olib boradi, siz haqingizdagi savollarga esa faqat bilimlar bazasidagi ma'lumot bilan javob beradi.

## Fayllar

- `knowledge/` — bilimlar bazasi. Shu papkaga `.md` yoki `.txt` fayllar qo'shasiz.
- `app.py` — Instagram webhook serveri.
- `agent.py` — javob yozadigan qism (qoidalar `SYSTEM` matnida).
- `kb.py` — bilimlar bazasidan qidirish.
- `chat.py` — Instagramsiz, terminalda sinash.

## 1. O'rnatish

```bash
pip install -r requirements.txt
```

```bash
cp .env.example .env
```

`.env` faylini ochib, `GEMINI_API_KEY` ga Gemini kalitingizni yozing.

## 2. Bilimlar bazasini to'ldirish

`knowledge/men-haqimda.md` faylini o'zingiz haqingizdagi ma'lumot bilan to'ldiring (yoki yangi fayllar qo'shing). `.env` dagi `OWNER_NAME` ga ismingizni yozing.

- Har bir mavzuni alohida abzats qilib, orasida bo'sh qator qoldiring.
- Fayllarni o'zgartirsangiz, serverni qayta ishga tushirish shart emas — keyingi xabarda yangi ma'lumot ishlatiladi.
- Siz haqingizdagi savolga bazada javob bo'lmasa, agent to'qimaydi — "o'zi ko'rishi bilan javob yozadi" deydi (`FALLBACK_TEXT`).
- Agent o'zini siz deb ko'rsatmaydi, AI yordamchi ekanini aytadi.

## 3. Terminalda sinash

```bash
python chat.py
```

## 4. Instagramga ulash

Kerak bo'ladi: Instagram **Business yoki Creator** akkaunt va internetdan ochiq HTTPS manzil (server yoki sinov uchun ngrok).

1. Serverni ishga tushiring:

   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

2. [developers.facebook.com](https://developers.facebook.com) da ilova yarating va unga **Instagram** mahsulotini qo'shing ("API setup with Instagram login").
3. Instagram akkauntingizni ulab, **access token** yarating → `.env` dagi `IG_ACCESS_TOKEN` ga yozing.
4. Ilovaning **App secret**ini `IG_APP_SECRET` ga yozing.
5. Webhook sozlamasida:
   - Callback URL: `https://sizning-manzil/webhook`
   - Verify token: `.env` dagi `IG_VERIFY_TOKEN` bilan bir xil so'z
   - `messages` maydoniga obuna bo'ling.
6. `.env` ni o'zgartirgach, serverni qayta ishga tushiring.

Ilova "Development" rejimida bo'lsa, faqat ilovaga rol berilgan akkauntlar yozgan xabarlarga javob boradi. Hammaga javob berish uchun Meta'da **App Review** dan o'tib, `instagram_business_manage_messages` ruxsatini olish kerak.

## Eslatmalar

- Suhbat tarixi (har bir suhbatdosh bilan oxirgi 10 ta xabar) xotirada saqlanadi, server o'chsa tozalanadi.
- Faqat matnli xabarlarga javob beriladi (rasm, ovozli xabar o'tkazib yuboriladi).
- Access token muddati 60 kun — uni vaqtida yangilab turing.
- Model `.env` dagi `GEMINI_MODEL` orqali almashtiriladi.
