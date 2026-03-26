import aiosqlite
import asyncio
from datetime import datetime, timedelta

DB_PATH = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT,
                role TEXT DEFAULT 'user',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                info TEXT,
                price TEXT,
                condition TEXT,
                owner_info TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id INTEGER NOT NULL,
                ad_id INTEGER NOT NULL,
                order_type TEXT,
                status TEXT DEFAULT 'pending',
                card_photo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buyer_id) REFERENCES users(telegram_id),
                FOREIGN KEY (ad_id) REFERENCES ads(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                plan_name TEXT,
                price INTEGER,
                paid_at TEXT,
                expires_at TEXT,
                status TEXT DEFAULT 'pending',
                card_photo TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        """)
        await db.commit()


# ─── USERS ───────────────────────────────────────────────────────────────────

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def create_user(telegram_id: int, full_name: str = None, phone: str = None, role: str = "user"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, full_name, phone, role) VALUES (?, ?, ?, ?)",
            (telegram_id, full_name, phone, role),
        )
        await db.commit()


async def update_user(telegram_id: int, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [telegram_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {fields} WHERE telegram_id = ?", values)
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def set_user_role(telegram_id: int, role: str):
    await update_user(telegram_id, role=role)


# ─── ADS ─────────────────────────────────────────────────────────────────────

async def create_ad(user_id: int, title: str, info: str, price: str, condition: str, owner_info: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO ads (user_id, title, info, price, condition, owner_info) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, title, info, price, condition, owner_info),
        )
        await db.commit()
        return cursor.lastrowid


async def get_ads(status: str = "active", limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ads WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_user_ads(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ads WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_ad(ad_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def delete_ad(ad_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM ads WHERE id = ? AND user_id = ?", (ad_id, user_id))
        await db.commit()


async def search_ads(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ads WHERE status = 'active' AND (title LIKE ? OR info LIKE ?) ORDER BY created_at DESC LIMIT 10",
            (f"%{query}%", f"%{query}%"),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


# ─── ORDERS ──────────────────────────────────────────────────────────────────

async def create_order(buyer_id: int, ad_id: int, order_type: str, card_photo: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO orders (buyer_id, ad_id, order_type, card_photo) VALUES (?, ?, ?, ?)",
            (buyer_id, ad_id, order_type, card_photo),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_orders(buyer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT o.*, a.title as ad_title, a.price as ad_price
            FROM orders o LEFT JOIN ads a ON o.ad_id = a.id
            WHERE o.buyer_id = ? ORDER BY o.created_at DESC
            """,
            (buyer_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_all_orders():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT o.*, a.title as ad_title, u.full_name as buyer_name, u.phone as buyer_phone
            FROM orders o
            LEFT JOIN ads a ON o.ad_id = a.id
            LEFT JOIN users u ON o.buyer_id = u.telegram_id
            ORDER BY o.created_at DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


# ─── SUBSCRIPTIONS ───────────────────────────────────────────────────────────

async def create_subscription(user_id: int, plan_name: str, price: int, card_photo: str, days: int):
    expires_at = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO subscriptions (user_id, plan_name, price, paid_at, expires_at, status, card_photo)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, 'pending', ?)
            ON CONFLICT(user_id) DO UPDATE SET
              plan_name=excluded.plan_name, price=excluded.price,
              paid_at=excluded.paid_at, expires_at=excluded.expires_at,
              status='pending', card_photo=excluded.card_photo
            """,
            (user_id, plan_name, price, expires_at, card_photo),
        )
        await db.commit()


async def get_subscription(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def approve_subscription(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE subscriptions SET status = 'active' WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def is_subscribed(user_id: int) -> bool:
    sub = await get_subscription(user_id)
    if not sub or sub["status"] != "active":
        return False
    expires_at = datetime.strptime(sub["expires_at"], "%Y-%m-%d %H:%M:%S")
    return expires_at > datetime.now()
