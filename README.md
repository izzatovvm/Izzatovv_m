# Instagram AI agent

Instagram direktiga yozgan do'stlar va yaqinlarga siz band bo'lganingizda Google Gemini API orqali javob beradigan shaxsiy AI yordamchi. Oddiy suhbatni o'zi olib boradi, siz haqingizdagi savollarga esa faqat bilimlar bazasidagi ma'lumot bilan javob beradi.

## Fayllar

- `knowledge/` — bilimlar bazasi. Shu papkaga `.md` yoki `.txt` fayllar qo'shasiz.
- `poll.py` — agentni ishga tushiradi (direktni tekshirib, javob beradi).
- `ig.py` — Instagram API bilan ishlash.
- `app.py` — ixtiyoriy webhook serveri.
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

Kerak bo'ladi: Instagram **Professional (Creator yoki Business)** akkaunt va Facebook akkaunt.

1. [developers.facebook.com](https://developers.facebook.com) da ilova yarating. Yaratish paytida **Content management** toifasidan **Manage messaging & content on Instagram** variantini tanlang.
2. Ilovaga biznes portfolio ulang (bepul, hujjat kerak emas).
3. **App roles → Roles → Add People → Instagram Tester** orqali Instagram akkauntingizni qo'shing va taklifni [instagram.com/accounts/manage_access](https://www.instagram.com/accounts/manage_access/) da (**Tester invites**) qabul qiling.
4. **Use cases → Customize → API setup with Unified login → Generate access tokens** bo'limida token yarating va `.env` dagi `IG_ACCESS_TOKEN` ga yozing.
5. Agentni ishga tushiring:

   ```bash
   python poll.py
   ```

Agent har 30 soniyada direktni tekshiradi va ishga tushgandan **keyin** kelgan yangi xabarlarga javob beradi; eski xabarlarga tegmaydi. Server, webhook yoki ochiq HTTPS manzil kerak emas — lekin `poll.py` ishlab turgan paytdagina javob beradi.

Sinash uchun: `DRY_RUN=1 python poll.py` hech narsa yubormaydi, faqat javobni ekranga chiqaradi. `.env` dagi `ONLY_USERNAMES` orqali faqat tanlangan akkauntlarga javob berishni cheklash mumkin.

`app.py` — ixtiyoriy webhook varianti (ochiq HTTPS manzilingiz bo'lsa): `uvicorn app:app --host 0.0.0.0 --port 8000`.

## Eslatmalar

- Suhbat tarixi Instagramning o'zidan olinadi (oxirgi bir necha xabar).
- Faqat matnli xabarlarga javob beriladi (rasm, ovozli xabar o'tkazib yuboriladi).
- Model `.env` dagi `GEMINI_MODEL` orqali almashtiriladi.
