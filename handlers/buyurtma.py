from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters,
)
import database as db
from keyboards import main_menu, cancel_kb, order_type_kb, confirm_kb
from config import CARD_NUMBER, CARD_OWNER, ADMIN_IDS

# States
ORD_AD_SEARCH, ORD_TYPE, ORD_CARD, ORD_CONFIRM = range(4)


# ─── BUYURTMA BERISH ─────────────────────────────────────────────────────────

async def order_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline tugma: 'Buyurtma berish' — ad_detail dan"""
    query = update.callback_query
    await query.answer()

    ad_id = int(query.data.split("_")[2])
    ad = await db.get_ad(ad_id)
    if not ad:
        await query.edit_message_text("❌ E'lon topilmadi.")
        return

    context.user_data["order_ad_id"] = ad_id
    context.user_data["order_ad_title"] = ad["title"]
    context.user_data["order_ad_price"] = ad["price"]

    await query.message.reply_text(
        f"🛒 <b>Buyurtma berish</b>\n\n"
        f"📦 <b>{ad['title']}</b>\n"
        f"💰 Narx: {ad['price']}\n\n"
        "Qanday olishni tanlang:",
        parse_mode="HTML",
        reply_markup=order_type_kb(),
    )
    return ORD_TYPE


async def ord_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        return await ord_cancel(update, context)

    context.user_data["order_type"] = "rent" if "Ijara" in text else "buy"
    type_label = "🔑 Ijaraga olish" if context.user_data["order_type"] == "rent" else "💳 Sotib olish"

    card_text = (
        f"💳 <b>To'lov</b>\n\n"
        f"Buyurtma turi: <b>{type_label}</b>\n\n"
        f"📌 To'lov kartasi:\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"👤 Egasi: <b>{CARD_OWNER}</b>\n\n"
        f"✅ To'lovni amalga oshiring va <b>chek rasmini</b> yuboring:"
    )
    await update.message.reply_text(card_text, parse_mode="HTML", reply_markup=cancel_kb())
    return ORD_CARD


async def ord_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.strip() == "❌ Bekor qilish":
        return await ord_cancel(update, context)

    photo = update.message.photo
    document = update.message.document

    if photo:
        context.user_data["order_card_photo"] = photo[-1].file_id
    elif document:
        context.user_data["order_card_photo"] = document.file_id
    else:
        await update.message.reply_text(
            "❌ Iltimos, chek <b>rasmini</b> yuboring:", parse_mode="HTML"
        )
        return ORD_CARD

    ad_title = context.user_data.get("order_ad_title", "")
    ad_price = context.user_data.get("order_ad_price", "")
    order_type = context.user_data.get("order_type", "buy")
    type_label = "🔑 Ijaraga olish" if order_type == "rent" else "💳 Sotib olish"

    await update.message.reply_text(
        f"📋 <b>Buyurtma tasdiqlash</b>\n\n"
        f"📦 Mahsulot: <b>{ad_title}</b>\n"
        f"💰 Narx: <b>{ad_price}</b>\n"
        f"🏷 Turi: <b>{type_label}</b>\n\n"
        "✅ Tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=confirm_kb(),
    )
    return ORD_CONFIRM


async def ord_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user

    if "Yo'q" in text or "Bekor" in text:
        return await ord_cancel(update, context)

    ad_id = context.user_data.get("order_ad_id")
    order_type = context.user_data.get("order_type", "buy")
    card_photo = context.user_data.get("order_card_photo")

    order_id = await db.create_order(
        buyer_id=user.id,
        ad_id=ad_id,
        order_type=order_type,
        card_photo=card_photo,
    )

    existing = await db.get_user(user.id)
    role = existing.get("role", "user") if existing else "user"

    await update.message.reply_text(
        f"🎉 <b>Buyurtma #{order_id} qabul qilindi!</b>\n\n"
        "⏳ Admin tekshiradi va siz bilan bog'lanadi.\n\n"
        "🙏 <i>Biz siz bilan har doim haq tanlamiz!</i>",
        parse_mode="HTML",
        reply_markup=main_menu(role),
    )

    # Admin xabardor qilish
    buyer_info = await db.get_user(user.id)
    ad = await db.get_ad(ad_id)
    type_label = "Ijaraga olish" if order_type == "rent" else "Sotib olish"

    admin_text = (
        f"🔔 <b>Yangi buyurtma #{order_id}</b>\n\n"
        f"👤 Xaridor: {buyer_info.get('full_name', '?')} | "
        f"{buyer_info.get('phone', '?')} | <a href='tg://user?id={user.id}'>Profil</a>\n"
        f"📦 Mahsulot: {ad['title'] if ad else '?'}\n"
        f"🏷 Turi: {type_label}\n"
        f"💰 Narx: {ad['price'] if ad else '?'}"
    )

    from keyboards import order_manage_inline
    for admin_id in ADMIN_IDS:
        try:
            await update.get_bot().send_message(
                admin_id, admin_text, parse_mode="HTML",
                reply_markup=order_manage_inline(order_id),
            )
            if card_photo:
                await update.get_bot().send_photo(admin_id, card_photo, caption="💳 Chek")
        except Exception:
            pass

    context.user_data.clear()
    return ConversationHandler.END


async def ord_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    role = user.get("role", "user") if user else "user"
    await update.message.reply_text("❌ Buyurtma bekor qilindi.", reply_markup=main_menu(role))
    context.user_data.clear()
    return ConversationHandler.END


# ─── BUYURTMALARIM ───────────────────────────────────────────────────────────

async def my_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    if not user or not user.get("phone"):
        await update.message.reply_text("⚠️ Avval /start bosib ro'yxatdan o'ting!")
        return

    orders = await db.get_user_orders(update.effective_user.id)
    if not orders:
        await update.message.reply_text(
            "📭 Sizda hali buyurtmalar yo'q.",
            reply_markup=main_menu(user.get("role", "user")),
        )
        return

    status_emoji = {
        "pending": "⏳",
        "confirmed": "✅",
        "rejected": "❌",
        "completed": "🏁",
    }
    lines = []
    for o in orders:
        emoji = status_emoji.get(o.get("status", "pending"), "•")
        type_label = "Ijara" if o.get("order_type") == "rent" else "Sotib olish"
        lines.append(
            f"{emoji} <b>#{o['id']}</b> — {o.get('ad_title', '?')} ({type_label}) | {o.get('created_at', '')[:10]}"
        )

    await update.message.reply_text(
        f"📋 <b>Buyurtmalarim</b> ({len(orders)} ta):\n\n" + "\n".join(lines),
        parse_mode="HTML",
        reply_markup=main_menu(user.get("role", "user")),
    )


# ─── ConversationHandler ─────────────────────────────────────────────────────

order_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(order_start_callback, pattern="^order_start_"),
    ],
    states={
        ORD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ord_type)],
        ORD_CARD: [
            MessageHandler(filters.PHOTO | filters.Document.ALL, ord_card),
            MessageHandler(filters.TEXT & ~filters.COMMAND, ord_card),
        ],
        ORD_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ord_confirm)],
    },
    fallbacks=[MessageHandler(filters.Regex("^❌ Bekor qilish$"), ord_cancel)],
    allow_reentry=True,
)
