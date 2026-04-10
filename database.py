import aiosqlite
from datetime import datetime, timezone, timedelta

DB_PATH = "bot.db"
TASHKENT = timezone(timedelta(hours=5))


def now_tashkent() -> str:
    return datetime.now(TASHKENT).strftime("%Y-%m-%d %H:%M:%S")


# ─── Init ─────────────────────────────────────────────────────────────────────

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                lang        TEXT    DEFAULT 'uz',
                joined_at   TEXT    DEFAULT (datetime('now')),
                is_blocked  INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                category    TEXT    NOT NULL,
                status      TEXT    NOT NULL DEFAULT 'pending',
                sent_at     TEXT    DEFAULT NULL,
                answered_at TEXT    DEFAULT NULL,
                rating      INTEGER DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                admin_id  INTEGER PRIMARY KEY,
                added_at  TEXT    DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id  INTEGER NOT NULL,
                admin_id    INTEGER NOT NULL,
                tg_msg_id   INTEGER NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """)
        await db.commit()


# ─── Users ────────────────────────────────────────────────────────────────────

async def upsert_user(user_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, lang)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lang = excluded.lang
        """, (user_id, lang))
        await db.commit()

async def get_active_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 0")
        row = await cursor.fetchone()
        return row[0] if row else 0

async def is_user_blocked(user_id: int) -> bool:
    """Foydalanuvchi bloklanganmi tekshiradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT is_blocked FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return bool(row[0]) if row else False

async def set_user_block_status(user_id: int, status: int):
    """Foydalanuvchini bloklaydi yoki blokdan chiqaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked = ? WHERE user_id = ?", (status, user_id))
        await db.commit()


# ─── Messages ─────────────────────────────────────────────────────────────────

async def save_message(user_id: int, category: str) -> int:
    """Xabarni DBga saqlaydi va uning id sini qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO messages (user_id, category, sent_at)
            VALUES (?, ?, ?)
        """, (user_id, category, now_tashkent()))
        await db.commit()
        return cursor.lastrowid

async def mark_answered(message_id: int):
    """Xabar holatini 'answered' ga o'zgartiradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE messages
            SET status = 'answered', answered_at = ?
            WHERE id = ?
        """, (now_tashkent(), message_id))
        await db.commit()

async def mark_reviewing(message_id: int):
    """Xabar holatini 'reviewing' ga o'zgartiradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE messages SET status = 'reviewing' WHERE id = ?
        """, (message_id,))
        await db.commit()

async def set_message_rating(message_id: int, rating: int):
    """Xabarga baho beradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE messages SET rating = ? WHERE id = ?
        """, (rating, message_id))
        await db.commit()

async def get_average_rating() -> float:
    """Barcha xabarlarning o'rtacha bahosini qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT AVG(rating) FROM messages WHERE rating IS NOT NULL")
        row = await cursor.fetchone()
        return round(row[0], 1) if row and row[0] else 0.0

async def get_message_user_id(message_id: int) -> int | None:
    """Xabar ID si bo'yicha foydalanuvchi ID sini qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id FROM messages WHERE id = ?", (message_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def get_last_message_status(user_id: int) -> dict | None:
    """Foydalanuvchining oxirgi xabari holatini qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, category, status, sent_at, answered_at
            FROM messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "id":          row[0],
            "category":    row[1],
            "status":      row[2],
            "sent_at":     row[3],
            "answered_at": row[4],
        }


# ─── Admin messages (sync tugmalar) ──────────────────────────────────────────

async def save_admin_message(message_id: int, admin_id: int, tg_msg_id: int):
    """Adminga yuborilgan Telegram xabar ID sini saqlaydi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO admin_messages (message_id, admin_id, tg_msg_id)
            VALUES (?, ?, ?)
        """, (message_id, admin_id, tg_msg_id))
        await db.commit()

async def get_admin_messages(message_id: int) -> list[dict]:
    """Xabar ID si bo'yicha barcha adminlarga yuborilgan tg_msg_id larni qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT admin_id, tg_msg_id FROM admin_messages
            WHERE message_id = ?
        """, (message_id,))
        rows = await cursor.fetchall()
        return [{"admin_id": r[0], "tg_msg_id": r[1]} for r in rows]


# ─── Stats ────────────────────────────────────────────────────────────────────

async def get_today_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT COUNT(*) FROM messages
            WHERE DATE(sent_at) = DATE('now', '+5 hours')
        """)
        row = await cursor.fetchone()
        return row[0] if row else 0

async def get_status_counts() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT status, COUNT(*) FROM messages GROUP BY status
        """)
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

async def get_category_counts() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT category, COUNT(*) FROM messages GROUP BY category
        """)
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

async def get_messages_by_category(category: str) -> list[dict]:
    """Kategoriya bo'yicha so'nggi 10 ta xabarni qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, user_id, status, sent_at
            FROM messages
            WHERE category = ?
            ORDER BY id DESC
            LIMIT 10
        """, (category,))
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "user_id": r[1], "status": r[2], "sent_at": r[3]}
            for r in rows
        ]

async def get_pending_messages() -> list[dict]:
    """Javob kutayotgan va ko'rib chiqilayotgan xabarlarni qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, user_id, category, status, sent_at
            FROM messages
            WHERE status IN ('pending', 'reviewing')
            ORDER BY id ASC
        """)
        rows = await cursor.fetchall()
        return [
            {
                "id":       r[0],
                "user_id":  r[1],
                "category": r[2],
                "status":   r[3],
                "sent_at":  r[4],
            }
            for r in rows
        ]

async def get_all_user_ids() -> list[int]:
    """Barcha foydalanuvchilar ID sini qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


# ─── Admins ───────────────────────────────────────────────────────────────────

async def get_all_admin_ids() -> list[int]:
    """Barcha adminlar ID sini qaytaradi (bosh admin bundan tashqari)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT admin_id FROM admins")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def add_admin(admin_id: int):
    """Yangi admin qo'shadi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO admins (admin_id) VALUES (?)
        """, (admin_id,))
        await db.commit()

async def remove_admin(admin_id: int):
    """Adminni o'chiradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE admin_id = ?", (admin_id,))
        await db.commit()
