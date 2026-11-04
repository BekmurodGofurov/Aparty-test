# Haftalik Hisobot (Weekly Project Report)

**Loyiha:** Aparty.uz  
**Dasturchi:** Bekmurod Gofurov  
**Mavzu:** Qidiruv sahifasi uchun backend (Server-Side) API filtrlash mexanizmi va tarmoq trafigini optimallashtirish  
**Sana:** Noyabr, 2026  
**Holat:** Muvaffaqiyatli yakunlandi va tizimga integratsiya qilindi  

---

## 📌 Qisqacha Xulosa (Executive Summary)

Ushbu haftada **Aparty.uz** loyihasining qidiruv va e'lonlar katalogi sahifasida (`PropertySearch`) ma'lumotlarni filtrlash arxitekturasi tubdan yangilandi va optimallashtirildi. 

Ilgari barcha e'lonlar mijoz (brauzer) tomoniga to'liq yuklab olinib, filtrlash faqat frontendda JavaScript (`filter`) orqali bajarilar edi. Bu esa katta hajmdagi ortiqcha ma'lumotlar trafigi sarflanishiga, sahifaning sekin ochilishiga hamda mobil qurilmalarda xotira (RAM) yuklanishiga olib kelardi.

Yangi yechimda **Server-Side API Filtering** yo'lga qo'yildi:
- Foydalanuvchi qidiruv parametrlarini (viloyat, tuman, narx oralig'i, xonalar soni, ijara turi, qulayliklar — Wi-Fi, konditsioner, kir yuvish mashinasi va h.k.) tanlaganda, bu filtrlar `GET /api/v1/listings/search` endpointiga query parametrlar sifatida yuboriladi.
- Backend va ma'lumotlar bazasi (PostgreSQL) indekslangan so'rovlar yordamida faqat kerakli e'lonlarni filtrlab, server paginatsiyasi (har bir sahifada 12 tadan) bilan qaytaradi.
- Natijada tarmoq trafigi keskin tejaladi, sahifa yuklanish tezligi oshadi va foydalanuvchi tajribasi (UX) yaxshilanadi.

---

## 1. 🔄 Nimadan Nimaga O'zgardi? (Client-Side vs Server-Side)

### 1.1. Avvalgi holat (Client-Side Filtering)
* **Katta tarmoq yuklamasi (Payload Overload):** Saytga kirganda minglab e'lonlar to'liq brauzerga yuklanar edi. Foydalanuvchi filtrni o'zgartirganda so'rov serverga bormasdan, frontend xotirasidagi massiv filtrlanardi.
* **Mobil internet va batareya sarfi:** Foydalanuvchi ko'rmaydigan yuzlab e'lonlar uchun ortiqcha megabaytlar sarflanar va mobil telefon protsessori zo'riqardi.
* **Masshtablash muammosi:** E'lonlar soni ortib borgan sari brauzer qotib qolishi va xotira to'lib ketishi xavfi mavjud edi.

### 1.2. Yangi holat (Server-Side API Filtering)
* **Tejamkor trafik va kichik payload:** Serverdan faqat hozirgi sahifaga kerakli bo'lgan 12 ta e'lon JSON formatida uzatiladi.
* **Ma'lumotlar bazasi darajasida filtrlash:** PostgreSQL indekslari (`btree`, `gin`) orqali minglab qatorlar ichidan bir necha millisoniyada mos yozuvlar topiladi.
* **URLSearchParams sinxronizatsiyasi:** Barcha filtrlar brauzer URL manziliga (`?region=Tashkent&price_min=100...`) yoziladi, natijada foydalanuvchi qidiruv natijalarini ulashishi (share) yoki xatcho'pga (bookmark) saqlashi mumkin.
* **Asinxron poyga holati (Race Condition) himoyasi:** Foydalanuvchi filtrlarni tez-tez o'zgartirganda, eski sekin so'rovlar yangi qidiruv natijalarining ustiga yozilib ketmasligi uchun so'rovlar hisoblagichi (`latestRequest`) joriy etildi.

### 1.3. Taqqoslash Jadvali

| Mezon | Avvalgi holat (Client-side) | Yangi holat (Server-side API) |
| :--- | :--- | :--- |
| **Filtrlash joyi** | Brauzer (Frontend JS) | Ma'lumotlar bazasi (Backend) |
| **Dastlabki yuklanish hajmi** | Katta (Barcha e'lonlar) | **Minimal (Faqat 12 ta e'lon)** |
| **Tarmoq trafigi sarfi** | Yuqori | **80-90% gacha tejaladi** |
| **Mobil qurilma xotira sarfi** | Ko'p (katta arraylar xotirada) | **Juda past (yengil DOM)** |
| **Paginatsiya** | Sun'iy (Frontend pagination) | Haqiqiy Server Paginatsiyasi (`limit`, `page`) |
| **URL Ulashish (Shareability)** | Cheklangan | `URLSearchParams` orqali to'liq qo'llab-quvvatlanadi |

---

## 2. 🧠 O'rganilgan Asosiy Bilimlar (Learn)

1. **RESTful API Filtering va Paginatsiya Standartlari:**
   - Katta to'plamlar (collections) bilan ishlashda server-side filtering va pagination arxitekturasining ahamiyati, `page` va `limit` parametrlarining maksimal chegaralarini belgilash (`safePageSize`).
2. **URLSearchParams va React Router integratsiyasi:**
   - Filtr holatlarini URL query string bilan sinxronlashtirish, sahifa yangilanganda ham filtrlarni saqlab qolish va navigatsiya tarixini to'g'ri boshqarish.
3. **Asinxron holatlarni boshqarish (Handling Race Conditions):**
   - Foydalanuvchi filtrlarni tezkor almashtirganda javoblarning navbati buzilib, eski so'rov natijasi yangisini bosib ketmasligini ta'minlash mexanizmi.
4. **Tarmoq samaradorligi va Web Performance:**
   - Tarmoq yukini (network payload) qisqartirish orqali Core Web Vitals ko'rsatkichlarini (LCP, INP, CLS) yaxshilash.

---

## 3. 📚 Foydalanilgan Rasmiy Manbalar (References)

* **Microsoft Azure Architecture Center:**  
  [RESTful Web API Design: Filtering and Paginating Data](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#filtering-and-paginating-data)  
  *Izoh: Katta ma'lumotlar to'plamida server darajasida filtrlash va paginatsiya qilish bo'yicha arxitektura qo'llanmasi.*

* **MDN Web Docs:**  
  [URLSearchParams API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams)  
  *Izoh: URL query satrlarini boshqarish va o'qish bo'yicha rasmiy hujjatlar.*

* **Google Cloud API Design Guide:**  
  [Standard Methods: List and Filter](https://cloud.google.com/apis/design/standard_methods#list)  
  *Izoh: API'larda ro'yxatlar va filtrlash parametrlarini loyihalash standartlari.*

* **Google Web.dev:**  
  [Reduce Network Payload Sizes](https://web.dev/articles/reduce-network-payload-sizes)  
  *Izoh: Tarmoq yuklamasini qisqartirish va veb tezligini oshirish amaliyotlari.*

* **MDN Web Docs:**  
  [Minimizing Payload Size for Web Performance](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Performance/Minimizing_payload_size)  
  *Izoh: Frontend va backend o'rtasida ma'lumot almashish hajmini optimallashtirish.*
