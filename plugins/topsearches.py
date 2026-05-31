# Search Analytics Plugin
# /topsearches — Top 10 most searched queries (admin + users)
# /clearsearches — Clear all analytics (admin only)

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import ADMINS

logger = logging.getLogger(__name__)


@Client.on_message(filters.command(["topsearches", "trending"]) & filters.incoming, group=-1)
async def top_searches_cmd(client, message):
    """Show top 10 most searched movie/series names"""
    sts = await message.reply_text("<b>⏳ Analytics fetch ho raha hai...</b>", parse_mode=enums.ParseMode.HTML)

    try:
        results = await db.get_top_searches(limit=10)
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return await sts.edit_text("<b>❌ Analytics fetch nahi ho sake!</b>", parse_mode=enums.ParseMode.HTML)

    if not results:
        return await sts.edit_text(
            "<b>📊 Abhi tak koi search nahi hua!</b>\n\n"
            "<i>Jab users search karenge, yahan dikhega.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    lines  = []
    for i, doc in enumerate(results):
        q     = doc.get("query", "Unknown")
        count = doc.get("count", 0)
        medal = medals[i] if i < len(medals) else f"{i+1}."
        lines.append(f"{medal} <b>{q}</b> — <code>{count}x</code>")

    total_unique = len(results)
    text = (
        f"<b>🔥 Top {total_unique} Trending Searches</b>\n\n"
        + "\n".join(lines)
        + "\n\n<i>Ye data real-time update hota hai!</i>"
    )

    btn = []
    if message.from_user and message.from_user.id in ADMINS:
        btn = [[InlineKeyboardButton("🗑 Clear Analytics", callback_data="clear_analytics_confirm")]]

    await sts.edit_text(
        text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(btn) if btn else None
    )


@Client.on_message(filters.command("clearsearches") & filters.user(ADMINS), group=-1)
async def clear_searches_cmd(client, message):
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Haan, Clear Karo", callback_data="clear_analytics_confirm"),
        InlineKeyboardButton("❌ Cancel",            callback_data="close_data")
    ]])
    await message.reply_text(
        "<b>⚠️ Saari search analytics delete karni hai?</b>\n\n"
        "<i>Ye action undo nahi ho sakta!</i>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=btn
    )


@Client.on_callback_query(filters.regex("^clear_analytics_confirm$"))
async def clear_analytics_cb(client, query):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf admin kar sakta hai!", show_alert=True)

    try:
        await db.clear_analytics()
        await query.answer("✅ Analytics clear kar diya!", show_alert=True)
        await query.message.edit_text(
            "<b>✅ Saari search analytics delete ho gayi!</b>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await query.answer(f"Error: {e}", show_alert=True)
