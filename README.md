# 🤖 ssanonymous-bot

> **O'zbek** | [**English**](#english)

---

## O'zbek tili 🇺🇿

Bo'stonliq Tumani Ixtisoslashtirilgan Maktabi uchun yaratilgan **anonim murojaat boti**.  
Foydalanuvchilar maktab adminlariga anonim tarzda taklif, shikoyat yoki savol yuborishi mumkin.

---

### ✨ Funksiyalar

#### 👥 Foydalanuvchilar uchun
| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni ishga tushirish |
| `/lang` | Tilni o'zgartirish (O'zbek / Rus / Ingliz) |
| `/anonim` | Anonim murojaat yuborish |
| `/status` | Oxirgi yuborilgan xabar holati |
| `/info` | Maktab haqida ma'lumot |
| `/links` | Telegram kanal va Discord server |

#### 🛡️ Adminlar uchun
| Buyruq | Tavsif |
|--------|--------|
| `/stats` | Bot statistikasi (kunlik, kategoriya, holat) |
| `/pending` | Javob kutayotgan xabarlar ro'yxati |

#### 👑 Bosh admin uchun
| Buyruq | Tavsif |
|--------|--------|
| `/broadcast` | Barcha foydalanuvchilarga xabar yuborish |
| `/addadmin` | Yangi admin qo'shish |
| `/removeadmin` | Adminni olib tashlash |
| `/admins` | Adminlar ro'yxatini ko'rish |
| `/cancel` | Amalni bekor qilish |

#### 🔔 Qo'shimcha imkoniyatlar
- **Ko'rib chiqdim** tugmasi — admin xabarni ko'rganida foydalanuvchiga bildirishnoma
- **Javob berish** tugmasi — admin to'g'ridan anonim foydalanuvchiga javob yuboradi
- **Admin sinxronizatsiyasi** — bir admin amal qilganda boshqa adminlarda ham yangilanadi
- **3 ta kategoriya** — Taklif, Shikoyat, Savol
- **Ko'p tilli** — O'zbek, Rus, Ingliz tillari

---

### 🛠️ Texnologiyalar

| Texnologiya | Versiya | Maqsad |
|------------|---------|--------|
| Python | 3.13+ | Asosiy dasturlash tili |
| aiogram | 3.x | Telegram Bot API |
| aiosqlite | latest | Asinxron SQLite |
| python-dotenv | latest | Environment variables |
| Railway | — | Hosting va deploy |

---

### 📁 Fayl tuzilmasi

```
ssanonymous-bot/
│
├── bot.py           # Asosiy bot kodi (handlerlar, state machine)
├── database.py      # SQLite bilan ishlash (CRUD funksiyalar)
├── LANGUAGES.py     # Ko'p tilli matnlar (uz, ru, en)
├── requirements.txt # Python kutubxonalari
└── README.md        # Loyiha haqida ma'lumot
```

---

### ⚙️ O'rnatish va ishga tushirish

#### 1. Repozitoriyani klonlash
```bash
git clone https://github.com/username/ssanonymous-bot.git
cd ssanonymous-bot
```

#### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

#### 3. Environment variables sozlash
`.env` fayli yarating:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
```

#### 4. Botni ishga tushirish
```bash
python bot.py
```

#### 5. Railway orqali deploy
1. GitHub repoga push qiling
2. [Railway](https://railway.app) da yangi project yarating
3. GitHub repo ni ulang
4. `BOT_TOKEN` va `ADMIN_ID` ni Variables ga qo'shing
5. Deploy avtomatik boshlanadi ✅

---

### 🗄️ Database jadvallari

```
users          — Foydalanuvchilar (user_id, lang, joined_at)
messages       — Xabarlar (id, user_id, category, status, sent_at, answered_at)
admins         — Adminlar (admin_id, added_at)
admin_messages — Admin-xabar bog'liqligi (message_id, admin_id, tg_msg_id)
```

---

---

## English 🇬🇧

An **anonymous appeal bot** for Bustanlik District Specialized School.  
Users can anonymously send suggestions, complaints, or questions to school administrators.

---

### ✨ Features

#### 👥 For Users
| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/lang` | Change language (Uzbek / Russian / English) |
| `/anonim` | Send an anonymous message |
| `/status` | Check the status of your last message |
| `/info` | Information about the school |
| `/links` | Telegram channel and Discord server |

#### 🛡️ For Admins
| Command | Description |
|---------|-------------|
| `/stats` | Bot statistics (daily, by category, by status) |
| `/pending` | List of unanswered messages |

#### 👑 For Super Admin
| Command | Description |
|---------|-------------|
| `/broadcast` | Send a message to all users |
| `/addadmin` | Add a new admin |
| `/removeadmin` | Remove an admin |
| `/admins` | View admin list |
| `/cancel` | Cancel current action |

#### 🔔 Additional Features
- **"Reviewing" button** — notifies the user when admin opens their message
- **"Reply" button** — admin can reply directly to the anonymous user
- **Admin sync** — when one admin acts, all other admins see the update
- **3 categories** — Suggestion, Complaint, Question
- **Multilingual** — Uzbek, Russian, English

---

### 🛠️ Tech Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.13+ | Core language |
| aiogram | 3.x | Telegram Bot API framework |
| aiosqlite | latest | Async SQLite database |
| python-dotenv | latest | Environment variables |
| Railway | — | Hosting & deployment |

---

### 📁 File Structure

```
ssanonymous-bot/
│
├── bot.py           # Main bot logic (handlers, state machine)
├── database.py      # SQLite layer (CRUD functions)
├── LANGUAGES.py     # Multilingual strings (uz, ru, en)
├── requirements.txt # Python dependencies
└── README.md        # Project documentation
```

---

### ⚙️ Setup & Deployment

#### 1. Clone the repository
```bash
git clone https://github.com/username/ssanonymous-bot.git
cd ssanonymous-bot
```

#### 2. Install dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure environment variables
Create a `.env` file:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
```

#### 4. Run locally
```bash
python bot.py
```

#### 5. Deploy on Railway
1. Push your code to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Add `BOT_TOKEN` and `ADMIN_ID` in the Variables tab
5. Railway will auto-deploy ✅

---

### 🗄️ Database Schema

```
users          — Users (user_id, lang, joined_at)
messages       — Messages (id, user_id, category, status, sent_at, answered_at)
admins         — Admins (admin_id, added_at)
admin_messages — Admin-message mapping (message_id, admin_id, tg_msg_id)
```

---

*Made with ❤️ for Bustanlik District Specialized School*
