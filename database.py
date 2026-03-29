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
                joined_at   TEXT    DEFAULT (datetime('now'))
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
                FOREIGN KEY (user_id) REFERENCES users(user_id)
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
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0


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
            UPDATE messages
            SET status = 'reviewing'
            WHERE id = ?
        """, (message_id,))
        await db.commit()

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

async def get_all_user_ids() -> list[int]:
    """Barcha foydalanuvchilar ID sini qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
