# Don't Remove Credit @VJ_Bots
# Telegraph / envs.sh File Upload — State-based (no pyromod needed)
# Command: /telegraph

import os, asyncio, requests
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# State store: user_id -> True (waiting for file)
TELEGRAPH_PENDING = {}


@Client.on_message(filters.command("telegraph"))
async def telegraph_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    TELEGRAPH_PENDING[user_id] = True
    await message.reply_text(
        "<b>📎 Photo ya Video bhejo (max 5MB)</b>\n\n"
        "❌ Cancel: /cancel",
        parse_mode=enums.ParseMode.HTML
    )


@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_telegraph(client, message):
    user_id = message.from_user.id
    if user_id in TELEGRAPH_PENDING:
        TELEGRAPH_PENDING.pop(user_id)
        await message.reply_text("✅ <b>Cancelled!</b>", parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.private & (filters.photo | filters.video | filters.document), group=6)
async def telegraph_file_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in TELEGRAPH_PENDING:
        return
    TELEGRAPH_PENDING.pop(user_id)

    status = await message.reply_text("<b>⬆️ Uploading...</b>", parse_mode=enums.ParseMode.HTML)
    file_path = None
    try:
        file_path = await message.download()
        file_size = os.path.getsize(file_path) / (1024 * 1024)

        if file_size > 5:
            return await status.edit(
                f"<b>❌ File bahut badi hai ({file_size:.1f}MB)\nMax 5MB allowed!</b>",
                parse_mode=enums.ParseMode.HTML
            )

        def _upload():
            with open(file_path, "rb") as f:
                r = requests.post("https://envs.sh", files={"file": f}, timeout=30)
            return r.text.strip() if r.status_code == 200 else None

        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(None, _upload)

        if not url:
            return await status.edit(
                "<b>❌ Upload fail hua! Dobara try karo.</b>",
                parse_mode=enums.ParseMode.HTML
            )

        await status.edit(
            f"<b>✅ Upload Ho Gaya!</b>\n\n"
            f"🔗 <b>Link:</b>\n<code>{url}</code>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔗 Open Link", url=url),
                InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={url}")
            ]])
        )
    except Exception as e:
        await status.edit(
            f"<b>❌ Error: <code>{str(e)[:150]}</code></b>",
            parse_mode=enums.ParseMode.HTML
        )
    finally:
        if file_path and os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
