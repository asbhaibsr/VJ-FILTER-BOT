# Don't Remove Credit @VJ_Bots
# Ads System Plugin
# /ad <title> <post_text_or_link> <image_url> <1week/1month/1year>

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from info import ADMINS, LOG_CHANNEL
from database.ads_db import add_ad, get_ad, delete_ad, list_ads, increment_click
from utils import temp

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
#  /ad command — Admin only
#  Usage: /ad <title> <post_text/link> <image_url> <duration>
# ══════════════════════════════════════════════
@Client.on_message(filters.command("ad") & filters.incoming)
async def add_ad_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply_text("❌ Sirf Admin ye command use kar sakta hai!")

    parts = message.text.split(None, 4)
    if len(parts) < 5:
        return await message.reply_text(
            "<b>❌ Format galat hai!</b>\n\n"
            "<b>Sahi format:</b>\n"
            "<code>/ad &lt;title&gt; &lt;post_text_ya_link&gt; &lt;image_url&gt; &lt;1week/1month/1year&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/ad \"Avengers 2025\" https://t.me/mychannel/123 https://image.url/poster.jpg 1week</code>\n\n"
            "• Title: Ad ka naam (results mein dikhega)\n"
            "• Post text/link: Telegram post link ya koi text\n"
            "• Image URL: Poster image URL\n"
            "• Duration: 1week / 1month / 1year",
            parse_mode=enums.ParseMode.HTML
        )

    _, title, content, image_url, duration = parts

    # Validate duration
    valid = any(x in duration.lower() for x in ["week", "month", "year", "day"])
    if not valid:
        return await message.reply_text("❌ Duration galat! Use: `1week`, `1month`, `1year`, `7day`")

    try:
        ad_id = add_ad(title, content, image_url, duration)
    except Exception as e:
        return await message.reply_text(f"❌ Ad add karne mein error: {e}")

    bot_link = f"https://t.me/{temp.U_NAME}?start=ad_{ad_id}"
    await message.reply_text(
        f"<b>✅ Ad Successfully Add Hua!</b>\n\n"
        f"📌 <b>Title:</b> {title}\n"
        f"⏳ <b>Duration:</b> {duration}\n"
        f"🔗 <b>Ad Start Link:</b> <code>{bot_link}</code>\n"
        f"🆔 <b>Ad ID:</b> <code>{ad_id}</code>\n\n"
        f"Ye ad search results ke neeche dikhega automatically.",
        parse_mode=enums.ParseMode.HTML
    )


# ══════════════════════════════════════════════
#  /delaد command — Delete an ad
# ══════════════════════════════════════════════
@Client.on_message(filters.command("delad") & filters.incoming)
async def del_ad_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return

    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("Usage: <code>/delad &lt;ad_id&gt;</code>",
                                        parse_mode=enums.ParseMode.HTML)

    ad_id = parts[1]
    if delete_ad(ad_id):
        await message.reply_text(f"✅ Ad `{ad_id}` delete ho gaya.")
    else:
        await message.reply_text(f"❌ Ad `{ad_id}` nahi mila ya already expire ho gaya.")


# ══════════════════════════════════════════════
#  /listads command — Show all active ads
# ══════════════════════════════════════════════
@Client.on_message(filters.command("listads") & filters.incoming)
async def list_ads_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return

    ads = list_ads()
    if not ads:
        return await message.reply_text("📭 Koi active ad nahi hai abhi.")

    text = "<b>📢 Active Ads:</b>\n\n"
    for ad in ads:
        remaining = ad["expires"] - __import__("datetime").datetime.utcnow()
        days = remaining.days
        text += (
            f"🆔 <code>{ad['_id']}</code>\n"
            f"📌 <b>{ad['title']}</b>\n"
            f"⏳ Expires in: {days} days\n"
            f"👆 Clicks: {ad.get('clicks', 0)}\n\n"
        )
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


# ══════════════════════════════════════════════
#  /start ad_<id> — Show ad post to user
# ══════════════════════════════════════════════
async def handle_ad_start(client, message, ad_id: str):
    """Called from commands.py start handler when data starts with 'ad_'"""
    ad = get_ad(ad_id)
    if not ad:
        return await message.reply_text(
            "❌ Ye ad expire ho gaya ya available nahi hai.",
            parse_mode=enums.ParseMode.HTML
        )

    increment_click(ad_id)

    content = ad["content"]
    title   = ad["title"]
    image   = ad["image"]

    # If content is a Telegram link, add as button
    is_link = content.startswith("http") or content.startswith("t.me")
    caption = f"<b>📢 {title}</b>"
    btn = []
    if is_link:
        btn.append([InlineKeyboardButton("🔗 View Post", url=content)])
    else:
        caption += f"\n\n{content}"

    markup = InlineKeyboardMarkup(btn) if btn else None

    try:
        await message.reply_photo(
            photo=image,
            caption=caption,
            reply_markup=markup,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        await message.reply_text(
            caption,
            reply_markup=markup,
            parse_mode=enums.ParseMode.HTML
        )
