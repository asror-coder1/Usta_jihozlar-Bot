# 🤖 Telegram Bot — Ishga tushirish qo'llanmasi

## 📁 Fayl tuzilishi

```
d:\TgBot\
├── bot.py              ← Asosiy kirish nuqtasi
├── config.py           ← Token, admin ID, tariflar
├── database.py         ← SQLite bazasi
├── keyboards.py        ← Barcha tugmalar
├── handlers/
│   ├── start.py        ← /start + ro'yxatdan o'tish
│   ├── elonlar.py      ← E'lon berish / E'lonlarim
│   ├── buyurtma.py     ← Buyurtma berish / Buyurtmalarim
│   ├── subscription.py ← Obuna (to'lov)
│   ├── usta.py         ← Usta topish + Bot haqida
│   └── admin.py        ← Admin panel
├── requirements.txt
└── .env                ← ⚠️ TOKEN SHU YERGA!
```

---

## ⚙️ 1-qadam: `.env` faylni sozlash

`.env` faylini oching va quyidagilarni to'ldiring:

```env
BOT_TOKEN=7xxxxxxxxx:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_IDS=123456789,987654321
CHANNEL_USERNAME=@your_channel
CARD_NUMBER=8600 1234 5678 9012
CARD_OWNER=Abdullayev Abdulla
```

- **BOT_TOKEN** — 8340444373:AAHJ_sML1gQ9sGCWZEoaWr7ZjyZreBywnPs
- **ADMIN_IDS** — 7499973776
- **CARD_NUMBER** — 9860170105907738
- **CARD_OWNER** — Ahror Fayzullayev

---

## 🚀 2-qadam: Ishga tushirish

```powershell
# Kutubxonalar o'rnatish (bir marta)
pip install -r requirements.txt

# Botni ishga tushirish
python bot.py
```

---

## 🛡 Bot funksiyalari

| Tugma | Tavsif |
|---|---|
| 📢 E'lon berish | Mahsulot/xizmat e'loni joylash (5 qadam) |
| 🛒 Buyurtma berish | E'londan buyurtma berish, to'lov yuborish |
| 👤 E'lonlarim | O'z e'lonlarini ko'rish va o'chirish |
| 📋 Buyurtmalarim | Barcha buyurtmalarni kuzatish |
| 💎 Obuna | 3 ta tarif: Boshlang'ich/Standart/Premium |
| 🔧 Usta topish | UstaZone platformasi ma'lumoti |
| ℹ️ Bot haqida | Bot haqida umumiy ma'lumot |
| 🛡 Admin panel | Faqat adminlar uchun boshqaruv paneli |

---

## 👮 Admin imkoniyatlari

- `/admin` yoki `🛡 Admin panel` tugmasi
- 👥 Foydalanuvchilar ro'yxati
- 📦 Barcha faol e'lonlar
- 🛒 Buyurtmalarni tasdiqlash / rad etish
- 💳 Obuna to'lovlarini tasdiqlash / rad etish
- 📊 Statistika

---

## 💡 Eslatma

- Bot to'xtatilganda ma'lumotlar `bot.db` faylida saqlanadi
- Obuna va buyurtma tasdiqlash — admin chatiga inline tugmalar orqali
- Xaridor va sotuvchilar tasdiqlanganda avtomatik xabar oladi
