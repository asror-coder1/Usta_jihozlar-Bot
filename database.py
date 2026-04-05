import sqlalchemy
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, MetaData,
    Table, create_engine, func
)
from databases import Database
from datetime import datetime, timedelta
from config import DB_URL

# Ma'lumotlar bazasiga ulanish ob'ekti
# DB_URL odatda "sqlite:///bot.db" ko'rinishida bo'ladi
database = Database(DB_URL)
metadata = MetaData()

# ─── JADVALLARNI ANIQLASH ──────────────────────────────────────────────────

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
    Column("user_id", Integer, nullable=False), # Telegram ID bilan bog'lanadi
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
    Column("paid_at", DateTime, server_default=func.now()),
    Column("expires_at", DateTime, nullable=True),
    Column("status", String, nullable=False, server_default="pending"),
    Column("card_photo", String, nullable=True),
)

# ─── BAZA BILAN ISHLASH (INIT/CLOSE) ──────────────────────────────────────

async def init_db():
    """Baza faylini yaratadi va jadvallarni shakllantiradi"""
    engine = create_engine(DB_URL)
    metadata.create_all(engine)
    if not database.is_connected:
        await database.connect()

async def close_db():
    """Baza ulanishini yopadi"""
    if database.is_connected:
        await database.disconnect()

# ─── FOYDALANUVCHILAR (USERS) ──────────────────────────────────────────────

async def get_user(telegram_id: int):
    query = users.select().where(users.c.telegram_id == telegram_id)
    row = await database.fetch_one(query)
    return dict(row) if row else None

async def create_user(telegram_id: int, full_name: str = None, phone: str = None, role: str = "user"):
    query = users.insert().values(
        telegram_id=telegram_id, 
        full_name=full_name, 
        phone=phone, 
        role=role
    )
    await database.execute(query)

async def update_user(telegram_id: int, **kwargs):
    if not kwargs: return
    query = users.update().where(users.c.telegram_id == telegram_id).values(**kwargs)
    await database.execute(query)

async def get_all_users():
    query = users.select().order_by(users.c.created_at.desc())
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]

# ─── E'LONLAR (ADS) ────────────────────────────────────────────────────────

async def create_ad(user_id: int, title: str, info: str, price: str, condition: str, owner_info: str):
    query = ads.insert().values(
        user_id=user_id, title=title, info=info, 
        price=price, condition=condition, owner_info=owner_info
    )
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

# ─── BUYURTMALAR (ORDERS) ──────────────────────────────────────────────────

async def create_order(buyer_id: int, ad_id: int, order_type: str, card_photo: str = None):
    query = orders.insert().values(
        buyer_id=buyer_id, ad_id=ad_id, 
        order_type=order_type, card_photo=card_photo
    )
    return await database.execute(query)

async def get_all_orders():
    # Buyurtmalarni e'lon sarlavhasi bilan birga olish (Join)
    query = sqlalchemy.select(
        [orders, ads.c.title.label("ad_title")]
    ).select_from(orders.join(ads, orders.c.ad_id == ads.c.id)).order_by(orders.c.created_at.desc())
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]

async def update_order_status(order_id: int, status: str):
    query = orders.update().where(orders.c.id == order_id).values(status=status)
    await database.execute(query)

# ─── OBUNALAR (SUBSCRIPTIONS) ───────────────────────────────────────────────

async def create_subscription(user_id: int, plan_name: str, price: int, card_photo: str, days: int):
    expires_at = datetime.now() + timedelta(days=days)
    
    # Avval bazada borligini tekshirish
    existing = await get_subscription(user_id)
    
    if existing:
        query = subscriptions.update().where(subscriptions.c.user_id == user_id).values(
            plan_name=plan_name,
            price=price,
            card_photo=card_photo,
            paid_at=func.now(),
            expires_at=expires_at,
            status="pending"
        )
    else:
        query = subscriptions.insert().values(
            user_id=user_id,
            plan_name=plan_name,
            price=price,
            card_photo=card_photo,
            expires_at=expires_at,
            status="pending"
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
    # Agar expires_at string bo'lsa (SQLite ba'zan shunday qaytaradi)
    if isinstance(expires_at, str):
        expires_at = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        
    return expires_at > datetime.now()

async def get_user_orders(buyer_id: int):
    # Bu funksiya foydalanuvchining buyurtmalarini e'lon ma'lumotlari bilan birga qaytaradi
    import sqlalchemy # Agar yuqorida import qilinmagan bo'lsa
    query = sqlalchemy.select(
        orders, ads.c.title.label("ad_title"), ads.c.price.label("ad_price")
    ).select_from(orders.join(ads, orders.c.ad_id == ads.c.id)).where(
        orders.c.buyer_id == buyer_id
    ).order_by(orders.c.created_at.desc())
    
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]