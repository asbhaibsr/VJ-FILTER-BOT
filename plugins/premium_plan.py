# Don't Remove Credit @VJ_Bots
# Premium Plan System - Bronze/Gold/Diamond with Screenshot/UTR Submit
# Fixed & Enhanced by Claude

import asyncio, logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.users_chats_db import db
from info import ADMINS, LOG_CHANNEL, PICS, PAYMENT_QR, OWNER_LNK, PREMIUM_AND_REFERAL_MODE
from utils import get_seconds, temp
import random, datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  Plan definitions — edit here as needed
# ─────────────────────────────────────────────
PLANS = [
    {
        "id": "bronze",
        "emoji": "🥉",
        "name": "Bronze Plan",
        "price": "₹30",
        "duration": "1 Week",
        "duration_code": "7day",
        "features": ["✅ No Verify Required", "✅ Direct Files", "✅ No Ads", "✅ Fast Access"],
        "color": "🟫",
    },
    {
        "id": "gold",
        "emoji": "🥇",
        "name": "Gold Plan",
        "price": "₹80",
        "duration": "1 Month",
        "duration_code": "1month",
        "features": ["✅ No Verify Required", "✅ Direct Files", "✅ No Ads", "✅ Fast Access", "✅ Request in 1hr"],
        "color": "🟡",
    },
    {
        "id": "diamond",
        "emoji": "💎",
        "name": "Diamond Plan",
        "price": "₹250",
        "duration": "6 Months",
        "duration_code": "6month",
        "features": ["✅ No Verify Required", "✅ Direct Files", "✅ No Ads", "✅ Fast Access",
                     "✅ Request in 1hr", "✅ VIP Support", "✅ Early Access"],
        "color": "🔷",
    },
]

def build_plan_text(plan):
    feats = "\n".join(plan["features"])
    return (
        f"<b>{plan['emoji']} {plan['name']} {plan['emoji']}</b>\n\n"
        f"💰 <b>Price:</b> {plan['price']}\n"
        f"⏳ <b>Duration:</b> {plan['duration']}\n\n"
        f"<b>🎁 Features:</b>\n{feats}\n\n"
        f"<i>UPI ID: <code>arsadsaifi8272@ibl</code></i>"
    )

def plan_nav_buttons(current_idx):
    plan = PLANS[current_idx]
    nav = []
    row = []
    if current_idx > 0:
        row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"plan_page#{current_idx - 1}"))
    row.append(InlineKeyboardButton(f"{current_idx + 1}/{len(PLANS)}", callback_data="plan_noop"))
    if current_idx < len(PLANS) - 1:
        row.append(InlineKeyboardButton("Next ➡️", callback_data=f"plan_page#{current_idx + 1}"))
    nav.append(row)
    nav.append([InlineKeyboardButton(f"💳 Buy {plan['name']} — {plan['price']}", callback_data=f"buy_plan#{plan['id']}")])
    nav.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="subscription")])
    return InlineKeyboardMarkup(nav)

# ─────────────────────────────────────────────
#  /plan command
# ─────────────────────────────────────────────
@Client.on_message(filters.command("plan") & filters.incoming)
async def plans_cmd_handler(client, message):
    if PREMIUM_AND_REFERAL_MODE == False:
        return
    plan = PLANS[0]
    await message.reply_photo(
        photo=PAYMENT_QR,
        caption=build_plan_text(plan),
        reply_markup=plan_nav_buttons(0),
        parse_mode=enums.ParseMode.HTML
    )

# ─────────────────────────────────────────────
#  Plan page navigation callback
# ─────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r"^plan_page#"))
async def plan_page_cb(client, query: CallbackQuery):
    idx = int(query.data.split("#")[1])
    plan = PLANS[idx]
    try:
        await query.message.edit_caption(
            caption=build_plan_text(plan),
            reply_markup=plan_nav_buttons(idx),
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex("^plan_noop$"))
async def plan_noop(client, query: CallbackQuery):
    await query.answer("Ye sirf page indicator hai 😊", show_alert=False)

# ─────────────────────────────────────────────
#  Buy plan button → ask for screenshot/UTR
# ─────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r"^buy_plan#"))
async def buy_plan_cb(client, query: CallbackQuery):
    plan_id = query.data.split("#")[1]
    plan = next((p for p in PLANS if p["id"] == plan_id), None)
    if not plan:
        return await query.answer("Plan not found!", show_alert=True)

    text = (
        f"<b>{plan['emoji']} {plan['name']} — {plan['price']} ({plan['duration']})</b>\n\n"
        f"📌 <b>Payment Steps:</b>\n"
        f"1️⃣ UPI ID: <code>arsadsaifi8272@ibl</code>\n"
        f"2️⃣ Amount: <b>{plan['price']}</b>\n"
        f"3️⃣ Screenshot ya UTR number leke neeche button dabao\n\n"
        f"⚠️ <i>Screenshot ya UTR bhejne ke baad Admin verify karega.</i>"
    )
    btn = [
        [InlineKeyboardButton("📸 Send Screenshot / UTR", callback_data=f"submit_payment#{plan_id}")],
        [InlineKeyboardButton("⬅️ Back to Plans", callback_data="plan_page#0")],
    ]
    try:
        await query.message.edit_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
    await query.answer()

# ─────────────────────────────────────────────
#  Submit payment — wait for screenshot/UTR
# ─────────────────────────────────────────────
PENDING_PAYMENT = {}  # user_id -> plan_id

@Client.on_callback_query(filters.regex(r"^submit_payment#"))
async def submit_payment_cb(client, query: CallbackQuery):
    plan_id = query.data.split("#")[1]
    plan = next((p for p in PLANS if p["id"] == plan_id), None)
    if not plan:
        return await query.answer("Plan not found!", show_alert=True)

    user_id = query.from_user.id
    PENDING_PAYMENT[user_id] = plan_id

    text = (
        f"📸 <b>Payment Proof Submit karo</b>\n\n"
        f"Plan: <b>{plan['emoji']} {plan['name']} — {plan['price']}</b>\n\n"
        f"✍️ Apna <b>Screenshot</b> ya <b>UTR Number</b> yahan bhejo.\n"
        f"(Screenshot image ya text UTR number — kuch bhi chalega)"
    )
    try:
        await query.message.edit_caption(caption=text, parse_mode=enums.ParseMode.HTML)
    except Exception:
        await client.send_message(user_id, text, parse_mode=enums.ParseMode.HTML)
    await query.answer("Ab screenshot ya UTR number bhejo 📸")

# ─────────────────────────────────────────────
#  Receive screenshot or UTR from user in PM
# ─────────────────────────────────────────────
@Client.on_message(filters.private & (filters.photo | filters.document | filters.text) & filters.incoming)
async def receive_payment_proof(client, message):
    user_id = message.from_user.id
    if user_id not in PENDING_PAYMENT:
        return  # Not waiting for payment from this user

    plan_id = PENDING_PAYMENT.pop(user_id)
    plan = next((p for p in PLANS if p["id"] == plan_id), None)
    if not plan:
        return

    user = message.from_user
    caption = (
        f"💰 <b>#PaymentProof</b>\n\n"
        f"👤 User: {user.mention} (<code>{user.id}</code>)\n"
        f"📦 Plan: <b>{plan['emoji']} {plan['name']} — {plan['price']} ({plan['duration']})</b>\n\n"
        f"<i>Neeche Accept ya Reject karo:</i>"
    )
    btn = [
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"prem_accept#{user_id}#{plan['duration_code']}#{plan['name']}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"prem_reject#{user_id}"),
        ]
    ]
    markup = InlineKeyboardMarkup(btn)

    try:
        if message.photo or message.document:
            # Forward media to LOG_CHANNEL with caption + buttons
            fwd = await message.forward(LOG_CHANNEL)
            await client.send_message(LOG_CHANNEL, caption, reply_markup=markup,
                                      reply_to_message_id=fwd.id, parse_mode=enums.ParseMode.HTML)
        else:
            # Text UTR
            full_caption = caption + f"\n\n📝 <b>UTR/Note:</b> <code>{message.text}</code>"
            await client.send_message(LOG_CHANNEL, full_caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Payment proof forward error: {e}")
        return

    await message.reply_text(
        f"<b>✅ Aapka payment proof bhej diya gaya!</b>\n\n"
        f"Plan: {plan['emoji']} <b>{plan['name']}</b>\n"
        f"⏳ Admin jaldi verify karega. Thoda wait karo 🙏",
        parse_mode=enums.ParseMode.HTML
    )

# ─────────────────────────────────────────────
#  Admin Accept callback
# ─────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r"^prem_accept#"))
async def prem_accept_cb(client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf Admin kar sakta hai!", show_alert=True)

    _, user_id, duration_code, plan_name = query.data.split("#", 3)
    user_id = int(user_id)

    seconds = await get_seconds(duration_code)
    expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    user_data = {"id": user_id, "expiry_time": expiry_time, "has_free_trial": True}
    await db.update_user(user_data)

    # Edit the log channel message
    try:
        await query.message.edit_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Accepted by {query.from_user.first_name}", callback_data="noop")]])
        )
    except Exception:
        pass

    # Notify user
    accept_text = (
        "👑 ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ 👑\n\n"
        "🙏 ʙᴀʜᴜᴛ-ʙᴀʜᴜᴛ ꜱʜᴜᴋʀɪʏᴀ! Aapki payment confirm ho gayi hai.\n\n"
        "🎬 ᴀʙ ᴍᴀᴢᴀ ʜɪ ᴍᴀᴢᴀ:\n"
        "●⚡ ᴅɪʀᴇᴄᴛ ꜰɪʟᴇꜱ & ɴᴏ ᴀᴅꜱ\n"
        "● 🚀 ᴜɴʟɪᴍɪᴛᴇᴅ ꜱᴘᴇᴇᴅ ᴀᴜʀ ᴀᴄᴄᴇꜱꜱ\n\n"
        "ᴠᴀʟɪᴅɪᴛʏ ᴄʜᴇᴄᴋ ᴋᴀʀᴇɪɴ: /myplan\n\n"
        "🎁 ꜰʀᴇᴇ ᴘʀᴇᴍɪᴜᴍ ᴡɪɴ ᴋᴀʀᴏ!\n"
        "Hamare channel @asbhai_bsr par har 1 taarikh ko FREE Premium ka Giveaway hota hai! "
        "Join karke ek 🔥 Reaction de den aur doston ko bhi batayen!\n\n"
        "Happy Streaming! 🎉"
    )
    try:
        await client.send_message(user_id, accept_text)
    except Exception as e:
        logger.error(f"Premium accept notify error: {e}")

    await query.answer(f"✅ Premium activated for user {user_id}!", show_alert=True)

# ─────────────────────────────────────────────
#  Admin Reject callback
# ─────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r"^prem_reject#"))
async def prem_reject_cb(client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf Admin kar sakta hai!", show_alert=True)

    _, user_id = query.data.split("#", 1)
    user_id = int(user_id)

    try:
        await query.message.edit_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton(f"❌ Rejected by {query.from_user.first_name}", callback_data="noop")]])
        )
    except Exception:
        pass

    reject_text = (
        "❌ <b>Payment Rejected</b>\n\n"
        "Aapka payment verify nahi ho saka.\n\n"
        "Reasons ho sakte hain:\n"
        "• Screenshot clear nahi tha\n"
        "• UTR invalid tha\n"
        "• Amount match nahi kiya\n\n"
        "Dobara try karo ya Admin se baat karo: " + OWNER_LNK
    )
    try:
        await client.send_message(user_id, reject_text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Premium reject notify error: {e}")

    await query.answer("❌ Payment rejected and user notified.", show_alert=True)

@Client.on_callback_query(filters.regex("^noop$"))
async def noop_cb(client, query: CallbackQuery):
    await query.answer()
