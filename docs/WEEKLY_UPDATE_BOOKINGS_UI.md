# Haftalik Hisobot (Weekly Project Report)

**Loyiha:** Aparty.uz  
**Dasturchi:** Latipov Shohruxbek  
**Mavzu:** Bron qilish sahifasi (`MyBookings`) UI qayta ishlab chiqilishi, Owner/User rollari ajratilishi va xatoliklarni bartaraf etish (Bug Fixing)  
**Sana:** Noyabr, 2026  
**Holat:** Muvaffaqiyatli yakunlandi va tizimga integratsiya qilindi  

---

## 📌 Qisqacha Xulosa (Executive Summary)

Ushbu haftada **Aparty.uz** platformasining eng muhim modullaridan biri bo'lgan **Bronlar boshqaruvi (My Bookings)** sahifasi to'liq qayta ko'rib chiqildi, mavjud xatoliklar (bug'lar) to'liq tuzatildi va interfeys foydalanuvchi tajribasiga (UX) moslab noldan yangilandi.

Ilgari ushbu sahifa ma'lumotlar sinxronizatsiyasidagi nosozliklar, oddiy ijarachi (talaba) va uy egasi (owner/makler) o'rtasidagi funksionallik to'g'ri ajratilmaganligi hamda API javoblaridagi kutilmagan `null` qiymatlar sababli to'g'ri ishlamas va qotib qolar edi.

Yangi yechimda:
- **Ikki tomonlama rol arxitekturasi:** Oddiy foydalanuvchilar o'zlari yuborgan bronlar ro'yxatini (`mine`) kuzatishlari, uy egalari esa o'z e'lonlariga kelgan tushgan buyurtmalarni (`incoming`) qabul qilish yoki rad etishlari uchun alohida tizim joriy etildi.
- **Glassmorphism UI va KPI ko'rsatkichlar:** Yangi zamonaviy shaffof dizayn tizimi (`GlassCard`), holat nishonlari (Pending, Confirmed, Rejected) hamda bronlar bo'yicha tezkor statistika (KPI) bloklari qo'shildi.
- **Bug fixing va ma'lumotlar xavfsizligi:** Keshdan tezkor chizish (`peekCache`), kunlar va narxlarni to'g'ri proporsional hisoblash hamda tasdiqlash modallari (`confirmModal`) yo'lga qo'yildi.

---

## 1. 🔄 Nimadan Nimaga O'zgardi? (Before vs After)

### 1.1. Avvalgi holat (Eski va ishlamaydigan holat)
* **Sahifa yuklanmasligi va xatoliklar:** Serverdan bo'sh massiv yoki noto'g'ri formatdagi ma'lumot kelganda sahifa butunlay oq bo'lib qolardi (White Screen of Death).
* **Rollarning aralashib ketishi:** Uy egasi va oddiy ijarachi uchun yagona va chalkash ko'rinish mavjud bo'lib, uy egalari tushgan arizalarni qulay boshqara olmas edi.
* **Harakatlar tasdiqlanmasligi:** Bronni bekor qilish yoki rad etishda xavfsizlik dialogi (modal) yo'qligi sababli tasodifiy xatolar yuzaga kelardi.

### 1.2. Yangi holat (Yangilangan arxitektura)
* **Avtomatik rol aniqlash:** Foydalanuvchi `owner` yoki `makler` bo'lsa, tizim avtomatik ravishda `incoming` (kelgan so'rovlar) tabiga yo'naltiradi.
* **Interaktiv status boshqaruvi:** Uy egalari har bir so'rovni bir bosish bilan `Qabul qilish` yoki `Rad etish` imkoniyatiga ega, bunda chiroyli tasdiqlash oynasi chiqadi.
* **Tezkor yuklanish va optimistik yangilanish:** Keshdan darhol chiziladi, status o'zgarganda sahifani qayta yuklamasdan faqat tegishli kartochka yangilanadi (`replaceById`).

---

## 2. 🧠 O'rganilgan Asosiy Bilimlar (Learn)

1. **Role-Based UI va Dynamic Tab Routing:**
   - React'da foydalanuvchi roli (`role`) asosida interfeysning ko'rinishini shartli renderlash (conditional rendering) va URL query parametrlari (`?tab=incoming`) bilan navigatsiyani bog'lash.
2. **Parallel API so'rovlari va Defensive Programming:**
   - `Promise.all` yordamida bir vaqtning o'zida bir nechta mustaqil so'rovlarni xavfsiz chaqirish (`.catch(() => [])`) va ma'lumotlar tuzilmasini doimo xavfsiz massiv ko'rinishida saqlash.
3. **Foydalanuvchi tajribasi (UX) va Modal Arxitekturasi:**
   - Muhim harakatlar (bekor qilish, rad etish) oldidan interaktiv modallar bilan foydalanuvchini ogohlantirish hamda harakat bajarilayotganda yuklanish animatsiyasini ko'rsatish (`actionLoadingId`).

---

## 3. 📚 Foydalanilgan Rasmiy Manbalar (References)

* **React Official Documentation:**  
  [Managing State and Component Lifecycle](https://react.dev/learn/managing-state)  
  *Izoh: React'da murakkab holatlarni to'g'ri boshqarish va renderlash qoidalari.*

* **React Official Documentation:**  
  [Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)  
  *Izoh: Komponentlar o'rtasida holatlarni sinxronlashtirish va lifting state up tamoyillari.*

* **Nielsen Norman Group:**  
  [Designing Effective Dashboards and Workflow UIs](https://www.nngroup.com/articles/designing-effective-dashboards/)  
  *Izoh: Bronlar va boshqaruv panellari uchun qulay va intuitiv foydalanuvchi interfeysini loyihalash qoidalari.*

* **MDN Web Docs:**  
  [ARIA: Dialog (Modal) Pattern and Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Roles/dialog_role)  
  *Izoh: Tasdiqlash modallari va muloqot oynalarining xavfsiz va qulay arxitekturasi.*

* **Refactoring UI:**  
  [Designing Clean Tables, Reservation Cards, and Status Badges](https://www.refactoringui.com/)  
  *Izoh: Ma'lumotlar kartalari, ranglar balansi va status ko'rsatkichlarini zamonaviy loyihalash.*
