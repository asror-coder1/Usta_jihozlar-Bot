from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters,
)
import database as db
from keyboards import (
    main_menu, cancel_kb, condition_kb, ads_inline,
    ad_detail_inline, my_ads_inline,
)

# States
AD_TITLE, AD_INFO, AD_PRICE, AD_CONDITION, AD_OWNER = range(5)


def _require_reg():
    async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = await db.get_user(update.effective_user.id)
        if not user or not user.get("phone"):
            await update.message.reply_text(
                "⚠️ Avval /start bosib ro'yxatdan o'ting!"
            )
            return ConversationHandler.END
        return None
    return check


# ─── E'LON BERISH ─────────────────────────────────────────────────────────────

async def elon_berish_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    if not user or not user.get("phone"):
        await update.message.reply_text("⚠️ Avval /start bosib ro'yxatdan o'ting!")
        return ConversationHandler.END

    await update.message.reply_text(
        "📢 <b>E'lon berish</b>\n\n"
        "1️⃣ Mahsulot / xizmat <b>nomini</b> kiriting:",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    return AD_TITLE


async def ad_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        return await ad_cancel(update, context)

    context.user_data["ad_title"] = text
    await update.message.reply_text(
        "2️⃣ Mahsulot haqida <b>batafsil ma'lumot</b> kiriting:",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    return AD_INFO


async def ad_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        return await ad_cancel(update, context)

    context.user_data["ad_info"] = text
    await update.message.reply_text(
        "3️⃣ <b>Narxini</b> kiriting (masalan: 150 000 so'm yoki Kelishiladi):",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    return AD_PRICE


async def ad_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        return await ad_cancel(update, context)

    context.user_data["ad_price"] = text
    await update.message.reply_text(
        "4️⃣ Mahsulot <b>holatini</b> tanlang:",
        parse_mode="HTML",
        reply_markup=condition_kb(),
    )
    return AD_CONDITION


async def ad_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        return await ad_cancel(update, context)

    context.user_data["ad_condition"] = text
    await update.message.reply_text(
        "5️⃣ <b>Egasi haqida ma'lumot</b> kiriting\n"
        "(Ism, telefon raqam yoki manzil):",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    return AD_OWNER


async def ad_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        return await ad_cancel(update, context)

    ud = context.user_data
    user = update.effective_user

    ad_id = await db.create_ad(
        user_id=user.id,
        title=ud.get("ad_title", ""),
        info=ud.get("ad_info", ""),
        price=ud.get("ad_price", ""),
        condition=ud.get("ad_condition", ""),
        owner_info=text,
    )

    existing = await db.get_user(user.id)
    role = existing.get("role", "user") if existing else "user"

    await update.message.reply_text(
        f"✅ <b>E'lon #{ad_id} muvaffaqiyatli joylashtirildi!</b>\n\n"
        f"📦 <b>Nomi:</b> {ud.get('ad_title')}\n"
        f"📝 <b>Ma'lumot:</b> {ud.get('ad_info')}\n"
        f"💰 <b>Narx:</b> {ud.get('ad_price')}\n"
        f"🔖 <b>Holat:</b> {ud.get('ad_condition')}\n"
        f"👤 <b>Egasi:</b> {text}",
        parse_mode="HTML",
        reply_markup=main_menu(role),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def ad_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    role = user.get("role", "user") if user else "user"
    await update.message.reply_text("❌ E'lon berish bekor qilindi.", reply_markup=main_menu(role))
    context.user_data.clear()
    return ConversationHandler.END


# ─── BUYURTMA BERISH (e'lonlar ro'yxatidan) ──────────────────────────────────

async def buyurtma_berish_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    if not user or not user.get("phone"):
        await update.message.reply_text("⚠️ Avval /start bosib ro'yxatdan o'ting!")
        return

    ads = await db.get_ads(status="active", limit=20)
    if not ads:
        await update.message.reply_text(
            "📭 Hozircha faol e'lonlar yo'q.\n\n"
            "Birinchi bo'lib e'lon bering! ↓",
            reply_markup=main_menu(user.get("role", "user")),
        )
        return

    await update.message.reply_text(
        "🛒 <b>Buyurtma berish</b>\n\n"
        "Quyidagi e'lonlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=ads_inline(ads),
    )


async def ad_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ad_id = int(query.data.split("_")[1])
    ad = await db.get_ad(ad_id)
    if not ad:
        await query.edit_message_text("❌ E'lon topilmadi yoki o'chirilgan.")
        return

    is_owner = ad["user_id"] == query.from_user.id

    text = (
        f"📦 <b>{ad['title']}</b>\n\n"
        f"📝 {ad['info']}\n\n"
        f"💰 <b>Narx:</b> {ad['price']}\n"
        f"🔖 <b>Holat:</b> {ad['condition']}\n"
        f"👤 <b>Egasi:</b> {ad['owner_info']}\n"
        f"📅 {ad['created_at'][:10]}"
    )
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=ad_detail_inline(ad_id, is_owner=is_owner),
    )


# ─── E'LONLARIM ──────────────────────────────────────────────────────────────

async def my_ads_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    if not user or not user.get("phone"):
        await update.message.reply_text("⚠️ Avval /start bosib ro'yxatdan o'ting!")
        return

    ads = await db.get_user_ads(update.effective_user.id)
    if not ads:
        await update.message.reply_text(
            "📭 Sizda hali e'lonlar yo'q.\n\n"
            "📢 «E'lon berish» tugmasini bosing!",
            reply_markup=main_menu(user.get("role", "user")),
        )
        return

    await update.message.reply_text(
        f"👤 <b>Sizning e'lonlaringiz</b> ({len(ads)} ta):\n\n"
        "E'lonni ko'rish yoki o'chirish uchun tanlang:",
        parse_mode="HTML",
        reply_markup=my_ads_inline(ads),
    )


async def my_ad_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ad_id = int(query.data.split("_")[2])
    ad = await db.get_ad(ad_id)
    if not ad:
        await query.edit_message_text("❌ E'lon topilmadi.")
        return

    text = (
        f"📦 <b>{ad['title']}</b> [#{ad['id']}]\n\n"
        f"📝 {ad['info']}\n"
        f"💰 Narx: {ad['price']}\n"
        f"🔖 Holat: {ad['condition']}\n"
        f"👤 Egasi: {ad['owner_info']}\n"
        f"📅 {ad['created_at'][:10]}"
    )
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 O'chirish", callback_data=f"del_ad_{ad_id}")]
    ])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)


async def delete_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ad_id = int(query.data.split("_")[2])
    await db.delete_ad(ad_id, query.from_user.id)
    await query.edit_message_text(f"🗑 E'lon #{ad_id} o'chirildi.")


# ─── ConversationHandler ─────────────────────────────────────────────────────

elon_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^📢 E'lon berish$"), elon_berish_start)],
    states={
        AD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_title)],
        AD_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_info)],
        AD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_price)],
        AD_CONDITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_condition)],
        AD_OWNER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ad_owner)],
    },
    fallbacks=[MessageHandler(filters.Regex("^❌ Bekor qilish$"), ad_cancel)],
    allow_reentry=True,
)
