# DB Backup Plugin
# /backup — Export key collections as JSON file (admin only)
# /cleanup — Delete expired/used redeem codes

import logging, json, os, datetime
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import ADMINS, DATABASE_NAME, LOG_CHANNEL

logger = logging.getLogger(__name__)


@Client.on_message(filters.command("backup") & filters.user(ADMINS), group=-1)
async def backup_cmd(client, message):
    """
    /backup         — Full backup (users + groups summary)
    /backup codes   — Only redeem codes backup
    /backup all     — Everything (large file)
    """
    args    = message.command
    mode    = args[1].lower() if len(args) > 1 else "summary"
    sts     = await message.reply_text("<b>⏳ Backup ban raha hai, thoda wait karo...</b>", parse_mode=enums.ParseMode.HTML)

    backup_data = {}
    timestamp   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename    = f"/tmp/backup_{mode}_{timestamp}.json"

    try:
        # ── ALWAYS include summary ──────────────────────────
        total_users = await db.total_users_count()
        total_chats = await db.total_chat_count()
        premium_count = await db.all_premium_users()
        codes_info  = await db.get_all_codes_count()

        backup_data["summary"] = {
            "exported_at":    datetime.datetime.now().isoformat(),
            "database_name":  DATABASE_NAME,
            "total_users":    total_users,
            "total_groups":   total_chats,
            "premium_users":  premium_count,
            "redeem_codes":   codes_info,
        }

        if mode in ("codes", "all"):
            # Export redeem codes
            codes = []
            async for doc in db.redeem.find({}):
                doc.pop("_id", None)
                if "created_at" in doc and isinstance(doc["created_at"], datetime.datetime):
                    doc["created_at"] = doc["created_at"].isoformat()
                if "expires_at" in doc and isinstance(doc["expires_at"], datetime.datetime):
                    doc["expires_at"] = doc["expires_at"].isoformat()
                if "used_at" in doc and isinstance(doc["used_at"], datetime.datetime):
                    doc["used_at"] = doc["used_at"].isoformat()
                codes.append(doc)
            backup_data["redeem_codes"] = codes

        if mode == "all":
            # Export premium users
            premium_users = []
            async for u in db.users.find({"expiry_time": {"$gt": datetime.datetime.now()}}):
                u.pop("_id", None)
                u.pop("ban_status", None)
                if "expiry_time" in u and isinstance(u["expiry_time"], datetime.datetime):
                    u["expiry_time"] = u["expiry_time"].isoformat()
                premium_users.append({"id": u.get("id"), "expiry": u.get("expiry_time")})
            backup_data["premium_users"] = premium_users

            # Export top searches
            top_s = await db.get_top_searches(50)
            for d in top_s:
                d.pop("_id", None)
                if "last_searched" in d and isinstance(d["last_searched"], datetime.datetime):
                    d["last_searched"] = d["last_searched"].isoformat()
            backup_data["top_searches"] = top_s

        # Write JSON file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        file_size = os.path.getsize(filename)
        size_str  = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/1024/1024:.1f} MB"

        caption = (
            f"<b>💾 Database Backup</b>\n\n"
            f"📦 Mode: <b>{mode}</b>\n"
            f"📅 Time: <code>{datetime.datetime.now().strftime('%d %b %Y %H:%M')}</code>\n"
            f"📊 Size: <b>{size_str}</b>\n\n"
            f"👥 Users: <b>{total_users}</b>\n"
            f"🏘 Groups: <b>{total_chats}</b>\n"
            f"💎 Premium: <b>{premium_count}</b>\n"
            f"🔑 Codes: Active={codes_info['active']} | Used={codes_info['used']}"
        )

        await sts.delete()
        await message.reply_document(
            document=filename,
            caption=caption,
            parse_mode=enums.ParseMode.HTML
        )

        # Log to LOG_CHANNEL
        try:
            await client.send_message(
                LOG_CHANNEL,
                f"💾 <b>#BackupCreated</b>\n"
                f"👤 {message.from_user.mention} (<code>{message.from_user.id}</code>)\n"
                f"📦 Mode: {mode} | Size: {size_str}",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Backup error: {e}")
        await sts.edit_text(f"<b>❌ Backup mein error aaya:</b>\n<code>{e}</code>", parse_mode=enums.ParseMode.HTML)
    finally:
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception:
            pass


@Client.on_message(filters.command("cleanup") & filters.user(ADMINS), group=-1)
async def cleanup_cmd(client, message):
    """Delete expired + used redeem codes from DB"""
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Haan, Cleanup Karo", callback_data="do_cleanup_codes"),
        InlineKeyboardButton("❌ Cancel",              callback_data="close_data")
    ]])

    codes_info = await db.get_all_codes_count()
    to_delete  = codes_info["used"] + codes_info["expired"]

    if to_delete == 0:
        return await message.reply_text(
            "<b>✅ Kuch cleanup karne ki zaroorat nahi!</b>\n\n"
            f"Active codes: <b>{codes_info['active']}</b>\n"
            f"Used codes: <b>{codes_info['used']}</b>\n"
            f"Expired codes: <b>{codes_info['expired']}</b>",
            parse_mode=enums.ParseMode.HTML
        )

    await message.reply_text(
        f"<b>🧹 Cleanup Preview</b>\n\n"
        f"Ye records delete honge:\n"
        f"• Used codes: <b>{codes_info['used']}</b>\n"
        f"• Expired codes: <b>{codes_info['expired']}</b>\n"
        f"• <b>Total: {to_delete}</b>\n\n"
        f"Active codes safe rahenge: <b>{codes_info['active']}</b>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=btn
    )


@Client.on_callback_query(filters.regex("^do_cleanup_codes$"))
async def do_cleanup_cb(client, query):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf admin kar sakta hai!", show_alert=True)

    try:
        deleted = await db.cleanup_expired_codes()
        await query.answer(f"✅ {deleted} codes delete kiye!", show_alert=True)
        await query.message.edit_text(
            f"<b>✅ Cleanup Complete!</b>\n\n"
            f"<b>{deleted}</b> expired/used redeem codes delete kiye gaye.",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await query.answer(f"Error: {e}", show_alert=True)
