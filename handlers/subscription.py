from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters,
)
import database as db
from keyboards import main_menu, cancel_kb, plans_inline, sub_approve_inline
from config import SUBSCRIPTION_PLANS, CARD_NUMBER, CARD_OWNER, ADMIN_IDS
from datetime import datetime

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
            # TUZATILDI: [:10] o'rniga xavfsiz strftime yoki string kesish
            expires_at = sub.get('expires_at')
            if isinstance(expires_at, datetime):
                date_str = expires_at.strftime('%d.%m.%Y')
            else:
                date_str = str(expires_at)[:10] if expires_at else "?"
                
            sub_status = (
                f"\n\n✅ <b>Faol obuna:</b> {sub.get('plan_name')}\n"
                f"📅 Tugash sanasi: {date_str}"
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

    # TUZATILDI: keyboards.py dagi 'plan_select_{key}' formatiga moslandi
    # split("_")[2] qilinadi, chunki format: plan_select_basic
    parts = query.data.split("_")
    if len(parts) < 3:
        await query.message.reply_text("❌ Xatolik: Callback ma'lumoti noto'g'ri.")
        return ConversationHandler.END
        
    plan_key = parts[2]
    plan = SUBSCRIPTION_PLANS.get(plan_key)
    
    if not plan:
        await query.message.reply_text("Tarif topilmadi!", show_alert=True)
        return ConversationHandler.END

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
    # Bekor qilish tugmasini tekshirish
    if update.message.text and update.message.text.strip() == "❌ Bekor qilish":
        return await sub_cancel(update, context)

    photo = update.message.photo
    document = update.message.document
    file_id = None

    if photo:
        file_id = photo[-1].file_id
    elif document and document.mime_type.startswith("image/"):
        file_id = document.file_id
    else:
        await update.message.reply_text("❌ Iltimos, chek <b>rasmini</b> yuboring:", parse_mode="HTML")
        return SUB_CARD

    plan = context.user_data.get("sub_plan", {})
    user_id = update.effective_user.id

    # Bazaga saqlash
    await db.create_subscription(
        user_id=user_id,
        plan_name=plan.get("name", ""),
        price=plan.get("price", 0),
        card_photo=file_id,
        days=plan.get("duration_days", 30),
    )

    user_db = await db.get_user(user_id)
    role = user_db.get("role", "user") if user_db else "user"

    await update.message.reply_text(
        "✅ <b>To'lov cheki qabul qilindi!</b>\n\n"
        "⏳ Adminlar tekshirib, 24 soat ichida obunangizni faollashtiradi.",
        parse_mode="HTML",
        reply_markup=main_menu(role),
    )

    # Adminlarni xabardor qilish
    admin_text = (
        f"💳 <b>Yangi obuna so'rovi</b>\n\n"
        f"👤 Foydalanuvchi: {user_db.get('full_name', '?')}\n"
        f"📱 Tel: {user_db.get('phone', '?')}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"💎 Tarif: {plan.get('name')}\n"
        f"💰 Summa: {plan.get('price', 0):,} so'm"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            # Rasm va tugmalarni yuborish
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=admin_text,
                parse_mode="HTML",
                reply_markup=sub_approve_inline(user_id)
            )
        except Exception as e:
            print(f"Admin {admin_id} ga xabar ketmadi: {e}")

    context.user_data.clear()
    return ConversationHandler.END


async def sub_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await db.get_user(update.effective_user.id)
    role = user.get("role", "user") if user else "user"
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_menu(role))
    context.user_data.clear()
    return ConversationHandler.END


sub_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(plan_chosen, pattern="^plan_select_")],
    states={
        SUB_CARD: [
            MessageHandler(filters.PHOTO | filters.Document.IMAGE, sub_card),
            MessageHandler(filters.TEXT & ~filters.COMMAND, sub_card),
        ],
    },
    fallbacks=[MessageHandler(filters.Regex("^❌ Bekor qilish$"), sub_cancel)],
    allow_reentry=True,
    per_message=False # Logdagi ogohlantirishni yo'qotadi
)