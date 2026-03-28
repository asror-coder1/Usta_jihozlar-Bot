import sqlalchemy
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, MetaData,
    Table, create_engine, func
)
from databases import Database

from config import DB_URL

database = Database(DB_URL)
metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("telegram_id", Integer, unique=True, nullable=False),
    Column("full_name", String, nullable=True),
    Column("phone", String, nullable=True),
    Column("role", String, nullable=False, server_default="user"),
    Column("created_at", DateTime, server_default=func.now()),
)

ads = Table(
    "ads",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("title", String, nullable=False),
    Column("info", Text, nullable=True),
    Column("price", String, nullable=True),
    Column("condition", String, nullable=True),
    Column("owner_info", String, nullable=True),
    Column("status", String, nullable=False, server_default="active"),
    Column("created_at", DateTime, server_default=func.now()),
)

orders = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("buyer_id", Integer, nullable=False),
    Column("ad_id", Integer, nullable=False),
    Column("order_type", String, nullable=True),
    Column("status", String, nullable=False, server_default="pending"),
    Column("card_photo", String, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)

subscriptions = Table(
    "subscriptions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False, unique=True),
    Column("plan_name", String, nullable=True),
    Column("price", Integer, nullable=True),
    Column("paid_at", DateTime, nullable=True),
    Column("expires_at", DateTime, nullable=True),
    Column("status", String, nullable=False, server_default="pending"),
    Column("card_photo", String, nullable=True),
)


async def init_db():
    engine = create_engine(DB_URL, future=True)
    metadata.create_all(engine)
    if not database.is_connected:
        await database.connect()


async def close_db():
    if database.is_connected:
        await database.disconnect()


async def get_user(telegram_id: int):
    query = users.select().where(users.c.telegram_id == telegram_id)
    row = await database.fetch_one(query)
    return dict(row) if row else None


async def create_user(telegram_id: int, full_name: str = None, phone: str = None, role: str = "user"):
    query = users.insert().values(telegram_id=telegram_id, full_name=full_name, phone=phone, role=role)
    await database.execute(query)


async def update_user(telegram_id: int, **kwargs):
    if not kwargs:
        return
    query = users.update().where(users.c.telegram_id == telegram_id).values(**kwargs)
    await database.execute(query)


async def get_all_users():
    query = users.select().order_by(users.c.created_at.desc())
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]


async def set_user_role(telegram_id: int, role: str):
    await update_user(telegram_id, role=role)


async def create_ad(user_id: int, title: str, info: str, price: str, condition: str, owner_info: str):
    query = ads.insert().values(user_id=user_id, title=title, info=info, price=price, condition=condition, owner_info=owner_info)
    return await database.execute(query)


async def get_ads(status: str = "active", limit: int = 20):
    query = ads.select().where(ads.c.status == status).order_by(ads.c.created_at.desc()).limit(limit)
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]


async def get_user_ads(user_id: int):
    query = ads.select().where(ads.c.user_id == user_id).order_by(ads.c.created_at.desc())
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]


async def get_ad(ad_id: int):
    query = ads.select().where(ads.c.id == ad_id)
    row = await database.fetch_one(query)
    return dict(row) if row else None


async def delete_ad(ad_id: int, user_id: int):
    query = ads.delete().where(ads.c.id == ad_id).where(ads.c.user_id == user_id)
    await database.execute(query)


async def search_ads(query_text: str):
    query = ads.select().where(
        (ads.c.status == "active") &
        ((ads.c.title.ilike(f"%{query_text}%")) | (ads.c.info.ilike(f"%{query_text}%")))
    ).order_by(ads.c.created_at.desc()).limit(10)
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]


async def create_order(buyer_id: int, ad_id: int, order_type: str, card_photo: str = None):
    query = orders.insert().values(buyer_id=buyer_id, ad_id=ad_id, order_type=order_type, card_photo=card_photo)
    return await database.execute(query)


async def get_user_orders(buyer_id: int):
    query = orders.select().where(orders.c.buyer_id == buyer_id).order_by(orders.c.created_at.desc())
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]


async def get_all_orders():
    query = orders.select().order_by(orders.c.created_at.desc())
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]


async def update_order_status(order_id: int, status: str):
    query = orders.update().where(orders.c.id == order_id).values(status=status)
    await database.execute(query)


from datetime import datetime, timedelta


async def create_subscription(user_id: int, plan_name: str, price: int, card_photo: str, days: int):
    expires_at = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    query = subscriptions.insert().values(
        user_id=user_id,
        plan_name=plan_name,
        price=price,
        paid_at=datetime.now(),
        expires_at=expires_at,
        status="pending",
        card_photo=card_photo,
    )
    await database.execute(query)


async def get_subscription(user_id: int):
    query = subscriptions.select().where(subscriptions.c.user_id == user_id)
    row = await database.fetch_one(query)
    return dict(row) if row else None


async def approve_subscription(user_id: int):
    query = subscriptions.update().where(subscriptions.c.user_id == user_id).values(status='active')
    await database.execute(query)


async def is_subscribed(user_id: int) -> bool:
    sub = await get_subscription(user_id)
    if not sub or sub.get('status') != 'active':
        return False
    expires_at = sub.get('expires_at')
    if not expires_at:
        return False
    if isinstance(expires_at, str):
        expires_at = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
    return expires_at > datetime.now()


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
