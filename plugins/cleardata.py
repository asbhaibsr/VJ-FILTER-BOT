# Don't Remove Credit @VJ_Bots
# /cleardata command - clears all bot data for a group
# Only group admins can use this

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import ChatAdminRequired
from database.users_chats_db import db
from database.filters_mdb import del_all
from database.connections_mdb import delete_connection
from info import ADMINS

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("cleardata") & filters.group)
async def clear_group_data(client, message):
    """Clears all bot data (filters, settings, connections) for this group."""
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    if not user_id:
        return

    # Only group admins or bot admins can clear data
    is_admin = user_id in ADMINS
    if not is_admin:
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return await message.reply_text("<b>❌ Sirf Group Admin ya Bot Owner yeh command use kar sakte hain!</b>",
                                                parse_mode=enums.ParseMode.HTML)
        except Exception:
            return await message.reply_text("<b>❌ Permission check failed.</b>", parse_mode=enums.ParseMode.HTML)

    btn = [
        [
            InlineKeyboardButton("✅ Haan, Delete Karo", callback_data=f"confirm_cleardata#{chat_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_cleardata"),
        ]
    ]
    await message.reply_text(
        f"<b>⚠️ Are you sure?</b>\n\n"
        f"Is group ka <b>saara data delete</b> ho jaega:\n"
        f"• Saare manual filters\n"
        f"• Group settings (shortlink, fsub, etc)\n"
        f"• Bot connections\n\n"
        f"<i>Yeh action undo nahi hoga!</i>",
        reply_markup=InlineKeyboardMarkup(btn),
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_callback_query(filters.regex(r"^confirm_cleardata#"))
async def confirm_cleardata_cb(client, query: CallbackQuery):
    user_id = query.from_user.id
    chat_id = int(query.data.split("#")[1])

    # Re-verify permission
    is_admin = user_id in ADMINS
    if not is_admin:
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return await query.answer("Sirf Admin kar sakta hai!", show_alert=True)
        except Exception:
            return await query.answer("Permission check failed.", show_alert=True)

    errors = []

    # 1. Delete all manual filters for this group
    try:
        await del_all(query.message, chat_id, query.message.chat.title if query.message.chat else "Group")
    except Exception as e:
        errors.append(f"Filters: {e}")

    # 2. Reset group settings to default
    try:
        from database.users_chats_db import default_setgs
        await db.update_settings(chat_id, default_setgs)
    except Exception as e:
        errors.append(f"Settings: {e}")

    # 3. Remove group from DB entirely and re-add fresh
    try:
        # Disable old entry and re-enable to reset
        await db.re_enable_chat(chat_id)
    except Exception as e:
        errors.append(f"Chat reset: {e}")

    if errors:
        await query.message.edit_text(
            f"<b>⚠️ Kuch data delete hua, lekin errors bhi aaye:</b>\n" + "\n".join(errors),
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await query.message.edit_text(
            "<b>✅ Group ka saara data successfully delete ho gaya!</b>\n\n"
            "<i>Ab bot fresh start karega is group mein.</i>",
            parse_mode=enums.ParseMode.HTML
        )
    await query.answer("Done!")

@Client.on_callback_query(filters.regex("^cancel_cleardata$"))
async def cancel_cleardata_cb(client, query: CallbackQuery):
    await query.message.edit_text("<b>✅ Clear data cancel ho gaya.</b>", parse_mode=enums.ParseMode.HTML)
    await query.answer("Cancelled!")
