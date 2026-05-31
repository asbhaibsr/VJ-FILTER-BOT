# Maintenance Mode Plugin
# Commands: /maintenance on [message] | /maintenance off | /maintenance status

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import ADMINS

logger = logging.getLogger(__name__)

# In-memory maintenance state (faster than DB read on every message)
# pm_filter.py reads this via info.MAINTENANCE_MODE,
# but we also maintain a live toggle here
_MAINTENANCE = {"on": False}


def is_maintenance() -> bool:
    return _MAINTENANCE["on"]


@Client.on_message(filters.command("maintenance") & filters.user(ADMINS), group=-1)
async def maintenance_cmd(client, message):
    """
    /maintenance on [custom message]
    /maintenance off
    /maintenance status
    """
    args = message.command

    if len(args) < 2:
        status = "🔴 ON" if _MAINTENANCE["on"] else "🟢 OFF"
        current_msg = await db.get_maintenance_msg()
        await message.reply_text(
            f"<b>🔧 Maintenance Mode: {status}</b>\n\n"
            f"<b>Current message:</b>\n<i>{current_msg}</i>\n\n"
            f"<b>Usage:</b>\n"
            f"<code>/maintenance on</code> — Enable\n"
            f"<code>/maintenance on Bot update chal raha hai, 10 min wait karo</code>\n"
            f"<code>/maintenance off</code> — Disable",
            parse_mode=enums.ParseMode.HTML
        )
        return

    action = args[1].lower()

    if action == "on":
        _MAINTENANCE["on"] = True
        # Update info module live
        try:
            import info as _info
            _info.MAINTENANCE_MODE = True
        except Exception:
            pass

        # Custom message set karo agar diya hai
        custom_msg = ""
        if len(args) > 2:
            custom_msg = " ".join(args[2:])
            await db.set_maintenance_msg(custom_msg)

        current_msg = await db.get_maintenance_msg()
        await message.reply_text(
            f"<b>🔴 Maintenance Mode: ON</b>\n\n"
            f"<b>Users ko dikhega:</b>\n<i>{current_msg}</i>\n\n"
            f"<i>Off karne ke liye: /maintenance off</i>",
            parse_mode=enums.ParseMode.HTML
        )
        try:
            await client.send_message(
                -1 * abs(int(str(message.chat.id))),
                None
            )
        except Exception:
            pass

    elif action == "off":
        _MAINTENANCE["on"] = False
        try:
            import info as _info
            _info.MAINTENANCE_MODE = False
        except Exception:
            pass
        await message.reply_text(
            "<b>🟢 Maintenance Mode: OFF</b>\n\n"
            "Bot ab normal mode mein hai. Sab users use kar sakte hain.",
            parse_mode=enums.ParseMode.HTML
        )

    elif action == "status":
        status = "🔴 ON" if _MAINTENANCE["on"] else "🟢 OFF"
        current_msg = await db.get_maintenance_msg()
        await message.reply_text(
            f"<b>Maintenance Status: {status}</b>\n\n"
            f"<b>Message:</b> <i>{current_msg}</i>",
            parse_mode=enums.ParseMode.HTML
        )

    else:
        await message.reply_text(
            "<b>❌ Invalid option!</b>\n\n"
            "Use: <code>/maintenance on</code> or <code>/maintenance off</code>",
            parse_mode=enums.ParseMode.HTML
        )


@Client.on_callback_query(filters.regex("^maintenance_off$"))
async def maintenance_off_cb(client, query):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf admin kar sakta hai!", show_alert=True)
    _MAINTENANCE["on"] = False
    try:
        import info as _info
        _info.MAINTENANCE_MODE = False
    except Exception:
        pass
    await query.answer("✅ Maintenance OFF kar diya!", show_alert=True)
    try:
        await query.message.edit_text(
            "<b>🟢 Maintenance Mode: OFF</b>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass
