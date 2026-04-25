# Don't Remove Credit @VJ_Bots
# Ads System Plugin — Step-by-step ad creation
# Commands: /ad  /delad  /listads  /ad_preview <ad_id>

import logging, datetime
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, ForceReply
)
from info import ADMINS, LOG_CHANNEL
from database.ads_db import add_ad, get_ad, delete_ad, list_ads, increment_click
from utils import temp

logger = logging.getLogger(__name__)

# State store: user_id -> step data
AD_STATES = {}

DURATION_MAP = {
    "1day": "1 Day", "3day": "3 Days", "7day": "1 Week",
    "2week": "2 Weeks", "1month": "1 Month", "3month": "3 Months",
    "6month": "6 Months", "1year": "1 Year"
}


# /ad command — Step 1: Start ad creation
@Client.on_message(filters.command("ad") & filters.incoming)
async def add_ad_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply_text(
            "❌ <b>Sirf Admin ye command use kar sakta hai!</b>",
            parse_mode=enums.ParseMode.HTML
        )
    user_id = message.from_user.id
    AD_STATES[user_id] = {"step": "title"}
    await message.reply_text(
        "<blockquote>"
        "<b>📢 Ad Create — Step 1/4</b>\n\n"
        "✏️ <b>Ad ka Title type karo:</b>\n"
        "<i>(Results mein ye title dikhega)</i>\n\n"
        "Example: <code>Pushpa 2 — Ab Available!</code>\n\n"
        "❌ Cancel: /cancel"
        "</blockquote>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=ForceReply(selective=True)
    )


# /cancel — Cancel ad creation
@Client.on_message(filters.command("cancel") & filters.private & filters.incoming)
async def cancel_ad_cmd(client, message):
    user_id = message.from_user.id
    if user_id in AD_STATES:
        AD_STATES.pop(user_id)
        return await message.reply_text(
            "✅ <b>Ad creation cancel ho gaya!</b>",
            parse_mode=enums.ParseMode.HTML
        )


# Step handler — handles all ad creation steps via private messages
@Client.on_message(filters.private & filters.incoming, group=5)
async def ad_step_handler(client, message):
    user_id = message.from_user.id
    if user_id not in AD_STATES:
        return
    if message.text and message.text.startswith("/"):
        return

    state = AD_STATES[user_id]
    step  = state.get("step")

    # Step 1: Title
    if step == "title":
        if not message.text or len(message.text.strip()) < 2:
            return await message.reply_text(
                "❌ <b>Title bahut chhota hai!</b>",
                parse_mode=enums.ParseMode.HTML
            )
        state["title"] = message.text.strip()
        state["step"]  = "content"
        await message.reply_text(
            "<blockquote>"
            "<b>📢 Ad Create — Step 2/4</b>\n\n"
            "🔗 <b>Post Link ya Text bhejo:</b>\n"
            "<i>(Telegram post link ya koi bhi text)</i>\n\n"
            "Examples:\n"
            "• <code>https://t.me/mychannel/123</code>\n"
            "• <code>Hamara naya channel join karo!</code>\n\n"
            "❌ Cancel: /cancel"
            "</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=ForceReply(selective=True)
        )

    # Step 2: Content
    elif step == "content":
        if not message.text or len(message.text.strip()) < 2:
            return await message.reply_text(
                "❌ <b>Content bahut chhota hai!</b>",
                parse_mode=enums.ParseMode.HTML
            )
        state["content"] = message.text.strip()
        state["step"]    = "image"
        await message.reply_text(
            "<blockquote>"
            "<b>📢 Ad Create — Step 3/4</b>\n\n"
            "🖼️ <b>Ad ki Photo bhejo:</b>\n"
            "<i>(Seedha photo upload karo — poster/banner)</i>\n\n"
            "💡 Agar photo nahi chahiye to <code>skip</code> likho.\n\n"
            "❌ Cancel: /cancel"
            "</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=ForceReply(selective=True)
        )

    # Step 3: Image
    elif step == "image":
        if message.photo:
            state["image"]      = message.photo.file_id
            state["image_type"] = "file_id"
        elif message.text and message.text.strip().lower() == "skip":
            state["image"]      = None
            state["image_type"] = None
        elif message.text and message.text.strip().startswith("http"):
            state["image"]      = message.text.strip()
            state["image_type"] = "url"
        else:
            return await message.reply_text(
                "❌ <b>Photo bhejo ya <code>skip</code> likho!</b>",
                parse_mode=enums.ParseMode.HTML
            )

        state["step"] = "duration"
        dur_buttons = [
            [
                InlineKeyboardButton("1 Day",    callback_data="ad_dur#1day"),
                InlineKeyboardButton("3 Days",   callback_data="ad_dur#3day"),
                InlineKeyboardButton("1 Week",   callback_data="ad_dur#7day"),
            ],
            [
                InlineKeyboardButton("2 Weeks",  callback_data="ad_dur#2week"),
                InlineKeyboardButton("1 Month",  callback_data="ad_dur#1month"),
                InlineKeyboardButton("3 Months", callback_data="ad_dur#3month"),
            ],
            [
                InlineKeyboardButton("6 Months", callback_data="ad_dur#6month"),
                InlineKeyboardButton("1 Year",   callback_data="ad_dur#1year"),
            ],
            [InlineKeyboardButton("❌ Cancel",   callback_data="ad_dur#cancel")],
        ]
        await message.reply_text(
            "<blockquote>"
            "<b>📢 Ad Create — Step 4/4</b>\n\n"
            "⏳ <b>Duration choose karo:</b>\n"
            "<i>(Kitne time tak results mein dikhega)</i>"
            "</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(dur_buttons)
        )


# Step 4: Duration callback
@Client.on_callback_query(filters.regex(r"^ad_dur#"))
async def ad_duration_cb(client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in AD_STATES or AD_STATES[user_id].get("step") != "duration":
        return await query.answer("❌ Koi active ad session nahi!", show_alert=True)

    choice = query.data.split("#")[1]
    if choice == "cancel":
        AD_STATES.pop(user_id, None)
        await query.message.edit_text(
            "✅ <b>Ad creation cancel ho gaya!</b>",
            parse_mode=enums.ParseMode.HTML
        )
        return await query.answer()

    state    = AD_STATES.pop(user_id)
    title    = state["title"]
    content  = state["content"]
    image    = state.get("image")
    img_type = state.get("image_type")
    duration = choice

    await query.answer("⏳ Ad save ho raha hai...")

    try:
        ad_id = add_ad(title, content, image, img_type, duration)
    except Exception as e:
        return await query.message.edit_text(
            f"❌ <b>Error:</b> <code>{e}</code>",
            parse_mode=enums.ParseMode.HTML
        )

    bot_link  = f"https://t.me/{temp.U_NAME}?start=ad_{ad_id}"
    dur_label = DURATION_MAP.get(duration, duration)

    success_text = (
        "<blockquote>"
        "✅ <b>Ad Successfully Create Ho Gaya!</b>\n\n"
        f"📌 <b>Title:</b> {title}\n"
        f"🔗 <b>Content:</b> {content[:60]}{'...' if len(content) > 60 else ''}\n"
        f"🖼️ <b>Image:</b> {'✅ Added' if image else '❌ Skipped'}\n"
        f"⏳ <b>Duration:</b> {dur_label}\n"
        f"🆔 <b>Ad ID:</b> <code>{ad_id}</code>\n\n"
        f"🔗 <b>Ad Link:</b>\n<code>{bot_link}</code>\n\n"
        "📢 Ye ab search results mein dikhega!\n"
        f"👁️ Preview: <code>/ad_preview {ad_id}</code>"
        "</blockquote>"
    )
    await query.message.edit_text(success_text, parse_mode=enums.ParseMode.HTML)

    try:
        await client.send_message(
            LOG_CHANNEL,
            f"📢 <b>#NewAd</b>\n\n"
            f"👤 By: {query.from_user.mention} (<code>{user_id}</code>)\n"
            f"📌 Title: {title}\n"
            f"⏳ Duration: {dur_label}\n"
            f"🆔 ID: <code>{ad_id}</code>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass


# /ad_preview <ad_id> — Preview
@Client.on_message(filters.command("ad_preview") & filters.incoming)
async def ad_preview_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: <code>/ad_preview &lt;ad_id&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )
    ad_id = message.command[1].strip()
    ad    = get_ad(ad_id)
    if not ad:
        return await message.reply_text(
            f"❌ <b>Ad <code>{ad_id}</code> nahi mila ya expire ho gaya!</b>",
            parse_mode=enums.ParseMode.HTML
        )
    await _send_ad_message(client, message.chat.id, ad)


# /delad <ad_id>
@Client.on_message(filters.command("delad") & filters.incoming)
async def del_ad_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: <code>/delad &lt;ad_id&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )
    ad_id = message.command[1].strip()
    if delete_ad(ad_id):
        await message.reply_text(
            f"✅ <b>Ad <code>{ad_id}</code> delete ho gaya!</b>",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(
            f"❌ <b>Ad <code>{ad_id}</code> nahi mila!</b>",
            parse_mode=enums.ParseMode.HTML
        )


# /listads
@Client.on_message(filters.command("listads") & filters.incoming)
async def list_ads_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return
    ads = list_ads()
    if not ads:
        return await message.reply_text(
            "📭 <b>Koi active ad nahi hai.</b>\n\nNaya ad: /ad",
            parse_mode=enums.ParseMode.HTML
        )
    text = "<blockquote><b>📢 Active Ads:</b></blockquote>\n\n"
    btns = []
    for ad in ads:
        remaining = ad["expires"] - datetime.datetime.utcnow()
        days = remaining.days
        hrs  = remaining.seconds // 3600
        time_left = f"{days}d {hrs}h" if days > 0 else f"{hrs}h"
        text += (
            f"━━━━━━━━━━━━━━\n"
            f"🆔 <code>{ad['_id']}</code>\n"
            f"📌 <b>{ad['title']}</b>\n"
            f"⏳ Expires in: <b>{time_left}</b>\n"
            f"👆 Clicks: <b>{ad.get('clicks', 0)}</b>\n\n"
        )
        btns.append([
            InlineKeyboardButton(
                f"🗑 {ad['title'][:25]}",
                callback_data=f"ad_delete#{ad['_id']}"
            )
        ])
    btns.append([InlineKeyboardButton("❌ Close", callback_data="close_data")])
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btns))


@Client.on_callback_query(filters.regex(r"^ad_delete#"))
async def ad_delete_cb(client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("❌ Admin only!", show_alert=True)
    ad_id = query.data.split("#")[1]
    if delete_ad(ad_id):
        await query.answer(f"✅ Ad deleted!", show_alert=True)
        ads = list_ads()
        if not ads:
            return await query.message.edit_text(
                "📭 <b>Saare ads delete ho gaye!</b>",
                parse_mode=enums.ParseMode.HTML
            )
        text = "<blockquote><b>📢 Active Ads:</b></blockquote>\n\n"
        btns = []
        for ad in ads:
            remaining = ad["expires"] - datetime.datetime.utcnow()
            days = remaining.days
            hrs  = remaining.seconds // 3600
            time_left = f"{days}d {hrs}h" if days > 0 else f"{hrs}h"
            text += (
                f"━━━━━━━━━━━━━━\n"
                f"🆔 <code>{ad['_id']}</code>\n"
                f"📌 <b>{ad['title']}</b>\n"
                f"⏳ Expires in: <b>{time_left}</b>\n"
                f"👆 Clicks: <b>{ad.get('clicks', 0)}</b>\n\n"
            )
            btns.append([
                InlineKeyboardButton(
                    f"🗑 {ad['title'][:25]}",
                    callback_data=f"ad_delete#{ad['_id']}"
                )
            ])
        btns.append([InlineKeyboardButton("❌ Close", callback_data="close_data")])
        await query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btns))
    else:
        await query.answer("❌ Ad nahi mila!", show_alert=True)


# Called from commands.py when /start ad_<id>
async def handle_ad_start(client, message, ad_id: str):
    ad = get_ad(ad_id)
    if not ad:
        return await message.reply_text(
            "❌ <b>Ye ad expire ho gaya!</b>",
            parse_mode=enums.ParseMode.HTML
        )
    increment_click(ad_id)
    await _send_ad_message(client, message.from_user.id, ad)


# Internal: send ad as beautiful message
async def _send_ad_message(client, chat_id: int, ad: dict):
    title    = ad["title"]
    content  = ad["content"]
    image    = ad.get("image")
    img_type = ad.get("image_type", "url")

    is_link = isinstance(content, str) and (content.startswith("http") or content.startswith("t.me"))
    caption = f"<b>📢 {title}</b>"
    if not is_link:
        caption += f"\n\n{content}"

    btn = []
    if is_link:
        btn.append([InlineKeyboardButton("🔗 ᴠɪᴇᴡ ᴘᴏꜱᴛ", url=content)])
    markup = InlineKeyboardMarkup(btn) if btn else None

    try:
        if image and img_type == "file_id":
            await client.send_photo(chat_id, photo=image, caption=caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        elif image and img_type == "url":
            await client.send_photo(chat_id, photo=image, caption=caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        else:
            await client.send_message(chat_id, caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception:
        await client.send_message(chat_id, caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
