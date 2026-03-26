from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton


# ─── MAIN MENU ────────────────────────────────────────────────────────────────

def main_menu(role: str = "user"):
    buttons = [
        ["📢 E'lon berish", "🛒 Buyurtma berish"],
        ["👤 E'lonlarim", "📋 Buyurtmalarim"],
        ["💎 Obuna", "🔧 Usta topish"],
        ["ℹ️ Bot haqida"],
    ]
    if role in ("admin", "superadmin"):
        buttons.append(["🛡 Admin panel"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def cancel_kb():
    return ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)


def back_kb():
    return ReplyKeyboardMarkup([["⬅️ Orqaga"]], resize_keyboard=True)


def phone_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)],
         ["❌ Bekor qilish"]],
        resize_keyboard=True,
    )


# ─── REGISTRATION ────────────────────────────────────────────────────────────

def skip_kb():
    return ReplyKeyboardMarkup([["➡️ O'tkazib yuborish"], ["❌ Bekor qilish"]], resize_keyboard=True)


# ─── E'LON BERISH ────────────────────────────────────────────────────────────

def condition_kb():
    return ReplyKeyboardMarkup(
        [["🟢 Yangi", "🟡 Yaxshi holat"], ["🟠 O'rtacha", "❌ Bekor qilish"]],
        resize_keyboard=True,
    )


# ─── BUYURTMA ────────────────────────────────────────────────────────────────

def order_type_kb():
    return ReplyKeyboardMarkup(
        [["💳 Sotib olish", "🔑 Ijaraga olish"], ["❌ Bekor qilish"]],
        resize_keyboard=True,
    )


def confirm_kb():
    return ReplyKeyboardMarkup(
        [["✅ Ha, tasdiqlash", "❌ Yo'q, bekor qilish"]],
        resize_keyboard=True,
    )


# ─── INLINE — ADS ────────────────────────────────────────────────────────────

def ads_inline(ads: list):
    buttons = []
    for ad in ads:
        buttons.append([
            InlineKeyboardButton(
                f"📦 {ad['title']} — {ad['price']}",
                callback_data=f"ad_{ad['id']}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


def ad_detail_inline(ad_id: int, is_owner: bool = False):
    buttons = [
        [InlineKeyboardButton("🛒 Buyurtma berish", callback_data=f"order_start_{ad_id}")]
    ]
    if is_owner:
        buttons.append([InlineKeyboardButton("🗑 O'chirish", callback_data=f"del_ad_{ad_id}")])
    return InlineKeyboardMarkup(buttons)


def my_ads_inline(ads: list):
    buttons = []
    for ad in ads:
        buttons.append([
            InlineKeyboardButton(f"📦 {ad['title']}", callback_data=f"myadview_{ad['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"del_ad_{ad['id']}"),
        ])
    return InlineKeyboardMarkup(buttons)


# ─── INLINE — SUBSCRIPTION ───────────────────────────────────────────────────

def plans_inline(plans: dict):
    buttons = []
    for key, plan in plans.items():
        buttons.append([
            InlineKeyboardButton(
                f"{plan['name']} — {plan['price']:,} so'm",
                callback_data=f"plan_{key}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


# ─── INLINE — ADMIN ──────────────────────────────────────────────────────────

def admin_main_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton("📦 Barcha e'lonlar", callback_data="admin_ads")],
        [InlineKeyboardButton("🛒 Barcha buyurtmalar", callback_data="admin_orders")],
        [InlineKeyboardButton("💳 To'lovlar (Obuna)", callback_data="admin_subs")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
    ])


def sub_approve_inline(user_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"sub_approve_{user_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"sub_reject_{user_id}"),
        ]
    ])


def order_manage_inline(order_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ord_ok_{order_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"ord_rej_{order_id}"),
        ]
    ])


def set_role_inline(user_tg_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 User", callback_data=f"role_user_{user_tg_id}")],
        [InlineKeyboardButton("🛡 Admin", callback_data=f"role_admin_{user_tg_id}")],
    ])
