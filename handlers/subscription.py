from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters,
)
import database as db
from keyboards import main_menu, cancel_kb, plans_inline, sub_approve_inline
from config import SUBSCRIPTION_PLANS, CARD_NUMBER, CARD_OWNER, ADMIN_IDS

# States
SUB_PLAN, SUB_CARD = range(2)


async def subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    if not user or not user.get("phone"):
        await update.message.reply_text("⚠️ Avval /start bosib ro'yxatdan o'ting!")
        return

    sub = await db.get_subscription(update.effective_user.id)
    sub_status = ""
    if sub:
        status = sub.get("status", "")
        if status == "active":
            sub_status = (
                f"\n\n✅ <b>Faol obuna:</b> {sub.get('plan_name')}\n"
                f"📅 Tugash sanasi: {sub.get('expires_at', '')[:10]}"
            )
        elif status == "pending":
            sub_status = "\n\n⏳ Obunangiz adminlar tomonidan tekshirilmoqda..."

    await update.message.reply_text(
        f"💎 <b>Obuna tanlash</b>{sub_status}\n\n"
        "Quyidagi tariflardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=plans_inline(SUBSCRIPTION_PLANS),
    )


async def plan_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_key = query.data.split("_")[1]
    plan = SUBSCRIPTION_PLANS.get(plan_key)
    if not plan:
        await query.answer("Tarif topilmadi!", show_alert=True)
        return

    context.user_data["sub_plan_key"] = plan_key
    context.user_data["sub_plan"] = plan

    await query.message.reply_text(
        f"💎 <b>{plan['name']}</b>\n\n"
        f"📋 {plan['description']}\n"
        f"💰 Narxi: <b>{plan['price']:,} so'm</b>\n\n"
        f"💳 To'lov uchun karta:\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"👤 Egasi: <b>{CARD_OWNER}</b>\n\n"
        "✅ To'lov qilgandan so'ng <b>chek rasmini</b> yuboring:",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    return SUB_CARD


async def sub_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.strip() == "❌ Bekor qilish":
        return await sub_cancel(update, context)

    photo = update.message.photo
    document = update.message.document

    if photo:
        file_id = photo[-1].file_id
    elif document:
        file_id = document.file_id
    else:
        await update.message.reply_text("❌ Iltimos, chek <b>rasmini</b> yuboring:", parse_mode="HTML")
        return SUB_CARD

    plan = context.user_data.get("sub_plan", {})
    user_id = update.effective_user.id

    await db.create_subscription(
        user_id=user_id,
        plan_name=plan.get("name", ""),
        price=plan.get("price", 0),
        card_photo=file_id,
        days=plan.get("duration_days", 30),
    )

    existing = await db.get_user(user_id)
    role = existing.get("role", "user") if existing else "user"

    await update.message.reply_text(
        "✅ <b>To'lov cheki qabul qilindi!</b>\n\n"
        "⏳ Adminlar tekshirib, 24 soat ichida obunangizni faollashtiradi.\n\n"
        "Savollar bo'lsa admin bilan bog'laning.",
        parse_mode="HTML",
        reply_markup=main_menu(role),
    )

    # Admin xabardor qilish
    user_db = await db.get_user(user_id)
    admin_text = (
        f"💳 <b>Yangi obuna so'rovi</b>\n\n"
        f"👤 Foydalanuvchi: {user_db.get('full_name', '?')}\n"
        f"📱 Tel: {user_db.get('phone', '?')}\n"
        f"🆔 ID: <a href='tg://user?id={user_id}'>{user_id}</a>\n"
        f"💎 Tarif: {plan.get('name')}\n"
        f"💰 Summa: {plan.get('price', 0):,} so'm"
    )
    for admin_id in ADMIN_IDS:
        try:
            await update.get_bot().send_message(
                admin_id, admin_text, parse_mode="HTML",
                reply_markup=sub_approve_inline(user_id),
            )
            await update.get_bot().send_photo(admin_id, file_id, caption="💳 To'lov cheki")
        except Exception:
            pass

    context.user_data.clear()
    return ConversationHandler.END


async def sub_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    role = user.get("role", "user") if user else "user"
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_menu(role))
    context.user_data.clear()
    return ConversationHandler.END


sub_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(plan_chosen, pattern="^plan_")],
    states={
        SUB_CARD: [
            MessageHandler(filters.PHOTO | filters.Document.ALL, sub_card),
            MessageHandler(filters.TEXT & ~filters.COMMAND, sub_card),
        ],
    },
    fallbacks=[MessageHandler(filters.Regex("^❌ Bekor qilish$"), sub_cancel)],
    allow_reentry=True,
)
