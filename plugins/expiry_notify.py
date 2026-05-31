# Premium Expiry Reminder Plugin
# Background task: Har ghante check karta hai, 24h pehle user ko remind karta hai
# /expirycheck — Admin manually trigger kar sake

import logging, asyncio, datetime
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import ADMINS, LOG_CHANNEL, PREMIUM_AND_REFERAL_MODE

logger = logging.getLogger(__name__)

_NOTIF_RUNNING = False  # Prevent duplicate tasks


async def send_expiry_reminders(client):
    """Sab users jinke premium 24h mein expire hone wale hain unhe remind karo"""
    if not PREMIUM_AND_REFERAL_MODE:
        return 0

    notified = 0
    try:
        expiring_users = await db.get_expiring_soon(hours=24)
        for user in expiring_users:
            user_id = user.get("id")
            if not user_id:
                continue
            # Agar already notified to skip
            if user.get("expiry_notified"):
                continue

            expiry_time = user.get("expiry_time")
            if not expiry_time:
                continue

            # Time remaining calculate karo
            remaining = expiry_time - datetime.datetime.now()
            hours_left = int(remaining.total_seconds() / 3600)
            mins_left  = int((remaining.total_seconds() % 3600) / 60)

            if hours_left > 0:
                time_str = f"{hours_left}h {mins_left}m"
            else:
                time_str = f"{mins_left} minutes"

            exp_str = expiry_time.strftime("%d %b %Y %I:%M %p")

            msg = (
                f"⚠️ <b>Premium Expiry Reminder!</b>\n\n"
                f"🕐 Sirf <b>{time_str}</b> bacha hai!\n"
                f"📅 Expiry: <code>{exp_str}</code>\n\n"
                f"Renew karo aur uninterrupted access enjoy karo! 🚀\n\n"
                f"💎 Renew karne ke liye: /plan"
            )
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("💎 Renew Now", callback_data="buy_premium"),
                InlineKeyboardButton("📊 My Plan",   callback_data="check_plan")
            ]])

            try:
                await client.send_message(
                    user_id, msg,
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=btn
                )
                await db.mark_expiry_notified(user_id)
                notified += 1
                await asyncio.sleep(0.5)   # Rate limit avoid karo
            except Exception as e:
                logger.debug(f"Could not notify user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Expiry reminder task error: {e}")

    return notified


async def expiry_reminder_loop(client):
    """Har 1 ghante mein check karta hai"""
    global _NOTIF_RUNNING
    if _NOTIF_RUNNING:
        return
    _NOTIF_RUNNING = True
    logger.info("Premium expiry reminder task started ✓")

    while True:
        try:
            count = await send_expiry_reminders(client)
            if count > 0:
                logger.info(f"Expiry reminders sent: {count}")
        except Exception as e:
            logger.error(f"Expiry loop error: {e}")
        await asyncio.sleep(3600)   # 1 hour


# ── Bot startup pe task start karo ─────────────────────────
# bot.py mein is function ko call karo jab bot start ho:
#   from plugins.expiry_notify import expiry_reminder_loop
#   asyncio.create_task(expiry_reminder_loop(TechVJBot))
# Ya yahan Client.on_message filter use karke first message pe start karein

_TASK_STARTED = False

@Client.on_message(filters.incoming, group=99)
async def start_expiry_task_once(client, message):
    """First message aate hi background task start karo (sirf ek baar)"""
    global _TASK_STARTED
    if not _TASK_STARTED:
        _TASK_STARTED = True
        asyncio.create_task(expiry_reminder_loop(client))
        logger.info("Expiry reminder background task launched ✓")


@Client.on_message(filters.command("expirycheck") & filters.user(ADMINS), group=-1)
async def expiry_check_cmd(client, message):
    """Admin manually trigger kare expiry reminders"""
    sts = await message.reply_text("<b>⏳ Expiring users check ho rahe hain...</b>", parse_mode=enums.ParseMode.HTML)

    # Show who's expiring soon
    expiring = await db.get_expiring_soon(hours=48)
    if not expiring:
        return await sts.edit_text(
            "<b>✅ Koi bhi premium agle 48 hours mein expire nahi ho raha!</b>",
            parse_mode=enums.ParseMode.HTML
        )

    lines = [f"<b>⚠️ {len(expiring)} users expire hone wale hain (48h):</b>\n"]
    for u in expiring[:20]:
        uid = u.get("id")
        exp = u.get("expiry_time")
        notified = "✅" if u.get("expiry_notified") else "❌"
        exp_str = exp.strftime("%d %b %H:%M") if exp else "?"
        lines.append(f"• <code>{uid}</code> — {exp_str} (notified: {notified})")

    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("📨 Send Reminders Now", callback_data="send_expiry_reminders"),
        InlineKeyboardButton("❌ Cancel",              callback_data="close_data")
    ]])

    await sts.edit_text(
        "\n".join(lines),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=btn
    )


@Client.on_callback_query(filters.regex("^send_expiry_reminders$"))
async def send_reminders_cb(client, query):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf admin!", show_alert=True)

    await query.answer("📨 Reminders bhej rahe hain...", show_alert=True)
    count = await send_expiry_reminders(client)
    try:
        await query.message.edit_text(
            f"<b>✅ {count} reminders bheje gaye!</b>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass


@Client.on_callback_query(filters.regex("^check_plan$"))
async def check_plan_cb(client, query):
    """Quick plan check from reminder button"""
    user_id = query.from_user.id
    if await db.has_premium_access(user_id):
        remaining = await db.check_remaining_usage(user_id)
        await query.answer(f"⏳ Remaining: {remaining}", show_alert=True)
    else:
        await query.answer("❌ Premium expire ho gaya! /plan se renew karo.", show_alert=True)
