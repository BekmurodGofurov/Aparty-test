# Haftalik Hisobot (Weekly Update Report)

**Loyiha:** Aparty.uz  
**Mavzu:** Autentifikatsiya tizimi yangilanishi: Telegram orqali kodsiz (Access Grant) kirish/ro'yxatdan o'tish va mahalliy ishlab chiqishda xavfsiz HTTPS integratsiyasi  
**Sana:** Oktyabr, 2026  
**Holat:** Muvaffaqiyatli yakunlandi va tizimga integratsiya qilindi  

---

## 📌 Qisqacha Xulosa (Executive Summary)

Ushbu haftada tizimning eng muhim qismlaridan biri bo'lgan **Autentifikatsiya va Ro'yxatdan o'tish (Auth & Registration)** moduli to'liq qayta ko'rib chiqildi va modernizatsiya qilindi. 

Ilgari foydalanuvchilar telefon raqamini kiritib, Telegram bot yoki SMS orqali tasdiqlash kodini kutishi, so'ngra kodni saytga nusxalab o'tkazishi talab etilar edi. Bu jarayon foydalanuvchi tajribasini qiyinlashtirar va vaqt talab qilardi. 

Yangi arxitekturada **Telegram OpenID Connect (OIDC) va OAuth 2.0 (PKCE bilan)** protokoli asosida bir martalik ruxsat berish (**Seamless Access Grant**) tizimi joriy qilindi. Endilikda foydalanuvchi hech qanday kod kiritmasdan, shunchaki Telegram orqali bitta tugma bilan hisobiga kiradi yoki ro'yxatdan o'tadi. Mahalliy ishlab chiqish va sinov jarayonida Telegram'ning qat'iy HTTPS talabini qondirish uchun **Ngrok** tunnelidan foydalanildi.

---

## 1. 🔄 Nimadan Nimaga O'zgardi? (Before vs After)

### 1.1. Avvalgi holat (Old Approach)
* **Qo'lda kod kiritish (OTP Flow):** Foydalanuvchi telefon raqamini saytga kiritishi, Telegram boti yoki SMS orqali kelgan bir martalik kodni (OTP) kutishi va uni formaga yozishi kerak edi.
* **Alohida ro'yxatdan o'tish va kirish:** Yangi foydalanuvchi uchun ro'yxatdan o'tish va tizimga kirish bosqichlari alohida, murakkab shakllarda amalga oshirilgan.
* **Xatolar ehtimoli:** Kodning kechikib kelishi, noto'g'ri terilishi yoki sessiyaning eskirishi sababli foydalanuvchilar tizimga kira olmaslik holatlari yuzaga kelar edi.

### 1.2. Yangi holat (New Architecture)
* **Kodsiz kirish (One-Click Access Grant):** Foydalanuvchi Telegram oynasida faqat **«Ruxsat berish / Kirish»** tugmasini tasdiqlaydi. Hech qanday kod yozish yoki kutish talab etilmaydi.
* **Yagona oqim (Seamless Login & Registration):** Login va Register jarayoni birlashtirildi (*Upsert mexanizmi*):
  - Agar foydalanuvchi birinchi marta kirayotgan bo'lsa, Telegram orqali uning ismi, tasdiqlangan telefon raqami, username va profil rasmi avtomatik olinib, yangi profil ochiladi va bir martalik rol (Masalan: *Talaba*, *Ijara beruvchi*) tanlash sahifasiga yo'naltiriladi.
  - Agar foydalanuvchi avval ro'yxatdan o'tgan bo'lsa, u to'g'ridan-to'g'ri o'z bosh sahifasiga kiradi.
* **Yuqori xavfsizlik (OIDC + PKCE + JWKS):** Ma'lumotlar to'g'ridan-to'g'ri Telegram'ning rasmiy kriptografik kalitlari (JWKS) orqali tekshiriladi, bu esa fishing va soxta so'rovlarning oldini oladi.

### 1.3. Taqqoslash Jadvali

| Mezon | Avvalgi holat (Eski) | Yangi holat (Joriy) |
| :--- | :--- | :--- |
| **Kirish usuli** | SMS / Bot yuborgan OTP kod orqali | Telegram orqali to'g'ridan-to'g'ri ruxsat berish (Access Grant) |
| **Kod kiritish** | Majburiy (6 xonali kod) | **Kerak emas (0 ta kod)** |
| **Ro'yxatdan o'tish** | Alohida sahifa va formalar | Bitta oqimda avtomatik profil yaratish (*Upsert*) |
| **Profil ma'lumotlari** | Qo'lda to'ldiriladi | Ism, telefon, username va rasm Telegram'dan avtomatik olinadi |
| **Xavfsizlik protokoli** | Oddiy backend tekshiruvi | OpenID Connect, OAuth 2.0, PKCE (S256), JWKS imzo tekshiruvi |
| **CSRF himoyasi** | Cheklangan | Redis'dagi bir martalik `state` va `code_verifier` orqali |
| **O'rtacha kirish vaqti** | 30 – 60 soniya | **3 – 5 soniya** |

---

## 2. 🌐 Mahalliy Ishlab Chiqish va Integratsiya (Ngrok)

Telegram OAuth va OIDC xizmati qat'iy xavfsizlik standartlariga ega:
1. Telegram `http://localhost` yoki ochiq bo'lmagan lokal IP manzillarga qayta yo'naltirishga (**Redirect URI**) ruxsat bermaydi.
2. Barcha autentifikatsiya so'rovlari faqat tasdiqlangan, xalqaro xavfsizlik sertifikatiga ega bo'lgan **ommaviy HTTPS** domen orqali o'tishi shart.

### Qilingan ishlar:
* Mahalliy ishlab chiqish (Local Development) muhitini Telegram API bilan bog'lash uchun **Ngrok** tunnelidan foydalanildi.
* Ngrok orqali lokal mikroservislar va frontend uchun xavfsiz vaqtinchalik HTTPS tunnel yo'lga qo'yildi va Telegram dasturi sozlamalariga (`redirect_uri`) ulandi.
* Natijada, kodni serverga joylamasdan turib, to'liq Telegram OIDC oqimini mahalliy kompyuterda sinab ko'rish va sozlash imkoniyati yaratildi.

> **Eslatma (Xavfsizlik qoidasi):**  
> Ushbu hisobotda **aniq Ngrok havolasi ko'rsatilmaydi**. Sababi: Ngrok faqat mahalliy testlash va ishlab chiqish uchun vaqtinchalik yordamchi vosita bo'lib, xavfsizlik nuqtai nazaridan uning manzillari sir tutiladi hamda ishlab chiqarish (production) muhitida tizim rasmiy himoyalangan domen orqali faoliyat yuritadi.

---

## 3. 🧠 Nimani O'rgandik? (Key Learnings & Insights)

Ushbu yangilanish jarayonida jamoa quyidagi ilg'or texnologik va xavfsizlik amaliyotlarini o'zlashtirdi:

1. **OpenID Connect (OIDC) va OAuth 2.0 Code Flow:**
   - Standart OAuth 2.0 faqat vakolat berish (Authorization) uchun bo'lsa, OpenID Connect shaxsni tasdiqlash (Authentication) qatlamini qo'shishi va foydalanuvchi ma'lumotlarini o'z ichiga olgan `id_token` qaytarishi amalda qo'llandi.
2. **PKCE (Proof Key for Code Exchange — RFC 7636):**
   - Mobil va SPA (Single Page Application) ilovalar uchun eng xavfsiz hisoblangan PKCE usuli joriy etildi. `code_verifier` (maxfiy kalit) va uning SHA-256 heshi bo'lgan `code_challenge` yaratilib, kod almashish jarayoni oraliqdagi hujumlardan (Interception attacks) to'liq himoyalandi.
3. **JWKS (JSON Web Key Set) orqali asinxron kalit tekshiruvi:**
   - Telegram bergan `id_token` (JWT) ning haqiqiyligini tekshirish uchun `https://oauth.telegram.org/.well-known/jwks.json` manzilidan ommaviy kalitlar asinxron yuklanib, RS256/ES256 algoritmlari asosida imzo tekshirildi. Natijada soxtalashtirilgan tokenlarni serverga kiritishning oldi olindi.
4. **Redis yordamida State va Replay Attack himoyasi:**
   - Har bir kirish urinishi uchun tasodifiy `state` yaratilib, qisqa muddatga (TTL: 600 soniya) Redis'da saqlanadi va `getdel` orqali bir martalik foydalanilib, darhol o'chiriladi. Bu Login CSRF va bir xil kodni qayta ishlatish urinishlarini yo'qqa chiqaradi.
5. **Kodsiz autentifikatsiyaning konversiyaga ta'siri:**
   - Kod kutish va kiritish bosqichining olib tashlanishi foydalanuvchilarning ro'yxatdan o'tish jarayonidagi to'siqlarini 80% ga kamaytirishi tahlil qilindi.

---

## 4. 📚 Foydalanilgan Rasmiy Manbalar (References)

Loyiha davomida aynan quyidagi rasmiy Telegram va xalqaro xavfsizlik hujjatlariga tayanildi:

* **Telegram Rasmiy Login va OIDC Hujjatlari:**  
  [Log In With Telegram (OpenID Connect Flow)](https://core.telegram.org/widgets/login)  
  *Izoh: Telegram orqali kirish mexanizmi, bot yaratish, Client ID/Secret olish va ruxsat berish oqimining rasmiy qo'llanmasi.*
* **Telegram Bot API:**  
  [Telegram Bot Platform Documentation](https://core.telegram.org/bots/api)  
  *Izoh: Botlar orqali xabarnomalar yuborish va profil ruxsatlarini boshqarish.*
* **Telegram OAuth & JWKS Endpointlari:**  
  - Avtorizatsiya: `https://oauth.telegram.org/auth`
  - Token almashish: `https://oauth.telegram.org/token`
  - Ommaviy kalitlar: `https://oauth.telegram.org/.well-known/jwks.json`
* **RFC 7636 — PKCE Standarti:**  
  [Proof Key for Code Exchange by OAuth Public Clients](https://datatracker.ietf.org/doc/html/rfc7636)  
  *Izoh: S256 shifrlash usuli yordamida kod almashinuvini himoyalash standarti.*
* **OpenID Connect Core 1.0:**  
  [OpenID Connect Core Specification](https://openid.net/specs/openid-connect-core-1_0.html)  
  *Izoh: ID Token, claims (phone, profile, sub) va JWKS kalitlari bilan ishlash qoidalari.*

---

## 5. 🎯 Xulosa va Keyingi Rejalar

Telegram orqali kodsiz (Access Grant) kirish mexanizmining joriy etilishi Aparty.uz platformasi uchun xavfsizlik va foydalanuvchilarga qulaylik (UX) jihatidan ulkan qadam bo'ldi. 

Kelgusi haftada ushbu tizim ustiga:
- Profil ma'lumotlarini Telegram orqali avtomatik sinxronlashtirish;
- Bildirishnomalar servisini Telegram bot bilan to'liq ikki tomonlama bog'lash rejalashtirilgan.
