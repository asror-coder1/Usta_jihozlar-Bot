from telegram import Update
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters,
)
import database as db
from keyboards import (
    main_menu, admin_main_inline, set_role_inline,
    order_manage_inline, sub_approve_inline,
)
from config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = await db.get_user(user.id)
    role = db_user.get("role", "user") if db_user else "user"

    if not is_admin(user.id) and role != "admin":
        await update.message.reply_text("🚫 Ruxsat yo'q.")
        return

    all_users = await db.get_all_users()
    all_ads = await db.get_ads(status="active")
    all_orders = await db.get_all_orders()

    await update.message.reply_text(
        f"🛡 <b>Admin Panel</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{len(all_users)}</b>\n"
        f"📦 Faol e'lonlar: <b>{len(all_ads)}</b>\n"
        f"🛒 Buyurtmalar: <b>{len(all_orders)}</b>",
        parse_mode="HTML",
        reply_markup=admin_main_inline(),
    )


async def admin_panel_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = await db.get_user(user.id)
    role = db_user.get("role", "user") if db_user else "user"

    if not is_admin(user.id) and role != "admin":
        await update.message.reply_text("🚫 Ruxsat yo'q.")
        return

    await admin_command(update, context)


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db_user = await db.get_user(query.from_user.id)
    role = db_user.get("role", "user") if db_user else "user"

    if not is_admin(query.from_user.id) and role != "admin":
        await query.answer("🚫 Ruxsat yo'q!", show_alert=True)
        return

    data = query.data

    # ─── Foydalanuvchilar ────────────────────────────────────────────────────
    if data == "admin_users":
        users = await db.get_all_users()
        if not users:
            await query.edit_message_text("👥 Foydalanuvchilar yo'q.")
            return

        lines = []
        for i, u in enumerate(users[:30], 1):
            lines.append(
                f"{i}. <b>{u.get('full_name', '?')}</b> | {u.get('phone', '?')} "
                f"| 🏷{u.get('role', 'user')} "
                f"| <a href='tg://user?id={u['telegram_id']}'>#{u['telegram_id']}</a>"
            )
        await query.edit_message_text(
            f"👥 <b>Foydalanuvchilar</b> ({len(users)}):\n\n" + "\n".join(lines),
            parse_mode="HTML",
            reply_markup=admin_main_inline(),
        )

    # ─── E'lonlar ────────────────────────────────────────────────────────────
    elif data == "admin_ads":
        ads = await db.get_ads(status="active", limit=20)
        if not ads:
            await query.edit_message_text("📦 Faol e'lonlar yo'q.", reply_markup=admin_main_inline())
            return

        lines = []
        for ad in ads:
            lines.append(
                f"• <b>#{ad['id']}</b> {ad['title']} | 💰{ad['price']} "
                f"| 👤uid:{ad['user_id']}"
            )
        await query.edit_message_text(
            f"📦 <b>Faol e'lonlar</b> ({len(ads)}):\n\n" + "\n".join(lines),
            parse_mode="HTML",
            reply_markup=admin_main_inline(),
        )

    # ─── Buyurtmalar ─────────────────────────────────────────────────────────
    elif data == "admin_orders":
        orders = await db.get_all_orders()
        if not orders:
            await query.edit_message_text("🛒 Buyurtmalar yo'q.", reply_markup=admin_main_inline())
            return

        status_emoji = {"pending": "⏳", "confirmed": "✅", "rejected": "❌", "completed": "🏁"}
        lines = []
        for o in orders[:20]:
            s = status_emoji.get(o.get("status", "pending"), "•")
            type_label = "Ijara" if o.get("order_type") == "rent" else "Sotib olish"
            lines.append(
                f"{s} <b>#{o['id']}</b> {o.get('ad_title', '?')} | "
                f"{type_label} | {o.get('buyer_name', '?')}"
            )
        await query.edit_message_text(
            f"🛒 <b>Buyurtmalar</b> ({len(orders)}):\n\n" + "\n".join(lines),
            parse_mode="HTML",
            reply_markup=admin_main_inline(),
        )

    # ─── Obunalar ────────────────────────────────────────────────────────────
    elif data == "admin_subs":
        from database import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute(
                "SELECT s.*, u.full_name, u.phone FROM subscriptions s "
                "LEFT JOIN users u ON s.user_id = u.telegram_id "
                "ORDER BY s.id DESC LIMIT 20"
            ) as cur:
                subs = [dict(r) for r in await cur.fetchall()]

        if not subs:
            await query.edit_message_text("💳 Obuna so'rovlari yo'q.", reply_markup=admin_main_inline())
            return

        lines = []
        for s in subs:
            status_e = {"pending": "⏳", "active": "✅", "rejected": "❌"}.get(s.get("status", ""), "•")
            lines.append(
                f"{status_e} <b>{s.get('full_name', '?')}</b> | {s.get('plan_name', '?')} "
                f"| {s.get('price', 0):,} so'm"
            )
        await query.edit_message_text(
            f"💳 <b>Obuna so'rovlari</b> ({len(subs)}):\n\n" + "\n".join(lines),
            parse_mode="HTML",
            reply_markup=admin_main_inline(),
        )

    # ─── Statistika ──────────────────────────────────────────────────────────
    elif data == "admin_stats":
        users = await db.get_all_users()
        ads = await db.get_ads(status="active")
        orders = await db.get_all_orders()

        pending_orders = [o for o in orders if o.get("status") == "pending"]

        await query.edit_message_text(
            f"📊 <b>Statistika</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{len(users)}</b>\n"
            f"📦 Faol e'lonlar: <b>{len(ads)}</b>\n"
            f"🛒 Jami buyurtmalar: <b>{len(orders)}</b>\n"
            f"⏳ Kutilayotgan buyurtmalar: <b>{len(pending_orders)}</b>",
            parse_mode="HTML",
            reply_markup=admin_main_inline(),
        )


# ─── Buyurtma tasdiqlash / rad etish ─────────────────────────────────────────

async def order_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    action = parts[1]  # ok yoki rej
    order_id = int(parts[2])

    if action == "ok":
        await db.update_order_status(order_id, "confirmed")
        status_text = "✅ Tasdiqlandi"

        # Xaridorni xabardor qilish
        orders = await db.get_all_orders()
        order = next((o for o in orders if o["id"] == order_id), None)
        if order:
            try:
                await query.get_bot().send_message(
                    order["buyer_id"],
                    f"✅ <b>Buyurtmangiz #{order_id} tasdiqlandi!</b>\n\n"
                    f"📦 {order.get('ad_title', '')}\n\n"
                    "Tez orada siz bilan bog'lanishadi.",
                    parse_mode="HTML",
                )
            except Exception:
                pass
    else:
        await db.update_order_status(order_id, "rejected")
        status_text = "❌ Rad etildi"

    await query.edit_message_text(
        f"{query.message.text}\n\n<b>{status_text}</b>",
        parse_mode="HTML",
    )


# ─── Obuna tasdiqlash / rad etish ────────────────────────────────────────────

async def sub_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    action = parts[1]  # approve yoki reject
    user_id = int(parts[2])

    if action == "approve":
        await db.approve_subscription(user_id)
        try:
            await query.get_bot().send_message(
                user_id,
                "🎉 <b>Obunangiz faollashtirildi!</b>\n\n"
                "Endi barcha imkoniyatlardan foydalanishingiz mumkin.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await query.edit_message_text(
            query.message.text + "\n\n✅ <b>Obuna faollashtirildi</b>",
            parse_mode="HTML",
        )
    else:
        try:
            await query.get_bot().send_message(
                user_id,
                "❌ <b>Obuna so'rovingiz rad etildi.</b>\n\n"
                "To'lov chekini qayta yuboring yoki admin bilan bog'laning.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await query.edit_message_text(
            query.message.text + "\n\n❌ <b>Rad etildi</b>",
            parse_mode="HTML",
        )


# ─── Rol o'rnatish ────────────────────────────────────────────────────────────

async def set_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("🚫 Ruxsat yo'q!", show_alert=True)
        return

    parts = query.data.split("_")
    new_role = parts[1]        # user yoki admin
    target_id = int(parts[2])

    await db.set_user_role(target_id, new_role)
    await query.edit_message_text(
        f"✅ Foydalanuvchi {target_id} roli → <b>{new_role}</b>",
        parse_mode="HTML",
    )
