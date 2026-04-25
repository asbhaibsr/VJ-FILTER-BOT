# Don't Remove Credit @VJ_Bots
# Telegraph / envs.sh File Upload
# Command: /telegraph

import os, requests, asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, Message
)


def _upload_file(file_path: str) -> str | None:
    """Upload file to envs.sh and return public URL"""
    try:
        with open(file_path, "rb") as f:
            resp = requests.post("https://envs.sh", files={"file": f}, timeout=30)
        if resp.status_code == 200:
            return resp.text.strip()
        return None
    except Exception as e:
        print(f"Upload error: {e}")
        return None


@Client.on_message(filters.command("telegraph"))
async def telegraph_cmd(client: Client, message: Message):
    status = await message.reply_text(
        "<b>📎 Photo ya Video bhejo (max 5MB)\n\n"
        "❌ Cancel karne ke liye /cancel bhejo</b>",
        parse_mode=enums.ParseMode.HTML
    )

    try:
        reply = await client.listen(
            message.chat.id,
            filters=filters.user(message.from_user.id),
            timeout=60
        )
    except asyncio.TimeoutError:
        return await status.edit(
            "<b>⏰ Timeout! Fir se /telegraph try karo.</b>",
            parse_mode=enums.ParseMode.HTML
        )

    if reply.text and reply.text.startswith("/cancel"):
        return await status.edit("<b>✅ Cancelled!</b>", parse_mode=enums.ParseMode.HTML)

    if not reply.media:
        return await status.edit(
            "<b>❌ Sirf Photo ya Video bhejo!</b>",
            parse_mode=enums.ParseMode.HTML
        )

    await status.edit("<b>⬆️ Uploading...</b>", parse_mode=enums.ParseMode.HTML)

    try:
        file_path = await reply.download()
        file_size = os.path.getsize(file_path) / (1024 * 1024)

        if file_size > 5:
            os.remove(file_path)
            return await status.edit(
                f"<b>❌ File bahut badi hai! ({file_size:.1f}MB)\nMax 5MB allowed hai.</b>",
                parse_mode=enums.ParseMode.HTML
            )

        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(None, _upload_file, file_path)

        if not url:
            return await status.edit(
                "<b>❌ Upload fail hua! Dobara try karo.</b>",
                parse_mode=enums.ParseMode.HTML
            )

        await status.edit(
            f"<b>✅ Upload Successful!</b>\n\n"
            f"🔗 <b>Link:</b>\n<code>{url}</code>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔗 Open Link", url=url),
                InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={url}")
            ],[
                InlineKeyboardButton("✗ Close", callback_data="close_data")
            ]])
        )

    except Exception as e:
        await status.edit(
            f"<b>❌ Error: <code>{str(e)[:150]}</code></b>",
            parse_mode=enums.ParseMode.HTML
        )
    finally:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
