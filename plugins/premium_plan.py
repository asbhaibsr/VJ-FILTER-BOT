# Don't Remove Credit @VJ_Bots
# Premium Plan System - Bronze / Gold / Diamond
# Screenshot/UTR Submit → Owner Accept/Reject

import asyncio, logging, datetime
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.users_chats_db import db
from info import ADMINS, LOG_CHANNEL, PAYMENT_QR, OWNER_LNK, PREMIUM_AND_REFERAL_MODE
from utils import get_seconds

logger = logging.getLogger(__name__)

# Plans — info.py ke PAYMENT_TEXT se sync hain
# Price/duration change karna ho to info.py mein PAYMENT_TEXT badlo
# Ya yahan seedha badlo — dono ek jaisi honi chahiye
PLANS = [
    {
        "id":            "bronze",
        "emoji":         "🥉",
        "name":          "Bronze Plan",
        "price":         "₹30",
        "duration":      "1 Week",
        "duration_code": "7day",
        "features":      [
            "✅ No Verify Required",
            "✅ Direct Files Milti Hain",
            "✅ No Ads",
            "✅ Fast Access",
        ],
    },
    {
        "id":            "gold",
        "emoji":         "🥇",
        "name":          "Gold Plan",
        "price":         "₹80",
        "duration":      "1 Month",
        "duration_code": "1month",
        "features":      [
            "✅ No Verify Required",
            "✅ Direct Files Milti Hain",
            "✅ No Ads",
            "✅ Fast Access",
            "✅ Movie Request (1hr mein)",
        ],
    },
    {
        "id":            "diamond",
        "emoji":         "💎",
        "name":          "Diamond Plan",
        "price":         "₹250",
        "duration":      "6 Months",
        "duration_code": "6month",
        "features":      [
            "✅ No Verify Required",
            "✅ Direct Files Milti Hain",
            "✅ No Ads",
            "✅ Fast Access",
            "✅ Movie Request (1hr mein)",
            "✅ VIP Support",
            "✅ Early Access to New Movies",
        ],
    },
]

# Track users who are submitting payment
PENDING_PAYMENT = {}


def _plan_caption(plan):
    feats = "\n".join(f"  {f}" for f in plan["features"])
    return (
        f"<b>{plan['emoji']}  {plan['name']}  {plan['emoji']}</b>\n\n"
        f"💰 <b>Price    :</b> <b>{plan['price']}</b>\n"
        f"⏳ <b>Duration :</b> <b>{plan['duration']}</b>\n\n"
        f"<b>🎁 Features:</b>\n{feats}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>UPI ID:</b> <code>arsadsaifi8272@ibl</code>\n"
        f"<i>Amount bhejo → Screenshot lo → Neeche Buy button dabao</i>"
    )


def _plan_buttons(idx):
    plan = PLANS[idx]
    nav_row = []
    if idx > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"vj_plan_pg#{idx - 1}"))
    nav_row.append(InlineKeyboardButton(f"📄 {idx + 1}/{len(PLANS)}", callback_data="vj_plan_noop"))
    if idx < len(PLANS) - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"vj_plan_pg#{idx + 1}"))
    return InlineKeyboardMarkup([
        nav_row,
        [InlineKeyboardButton(
            f"💳 Buy {plan['name']} — {plan['price']}",
            callback_data=f"vj_buy_plan#{plan['id']}"
        )],
        [InlineKeyboardButton("🔙 Close", callback_data="close_data")],
    ])


@Client.on_message(filters.command("plan") & filters.incoming, group=-1)
async def plan_cmd(client, message):
    if not PREMIUM_AND_REFERAL_MODE:
        return await message.reply_text(
            "<b>Premium mode abhi disabled hai.</b>",
            parse_mode=enums.ParseMode.HTML
        )
    plan    = PLANS[0]
    caption = _plan_caption(plan)
    markup  = _plan_buttons(0)
    try:
        if PAYMENT_QR and PAYMENT_QR.startswith("http"):
            await message.reply_photo(
                photo=PAYMENT_QR,
                caption=caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            raise ValueError("No valid QR URL")
    except Exception:
        # Fallback: plain text with plan info
        await message.reply_text(
            caption,
            reply_markup=markup,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )


@Client.on_callback_query(filters.regex(r"^vj_plan_pg#"), group=0)
async def plan_page_cb(client, query: CallbackQuery):
    idx  = int(query.data.split("#")[1])
    plan = PLANS[idx]
    try:
        await query.message.edit_caption(
            caption=_plan_caption(plan),
            reply_markup=_plan_buttons(idx),
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        try:
            await query.message.edit_text(
                _plan_caption(plan),
                reply_markup=_plan_buttons(idx),
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass
    await query.answer()


@Client.on_callback_query(filters.regex("^vj_plan_noop$"), group=0)
async def plan_noop_cb(client, query: CallbackQuery):
    await query.answer("Ye sirf page number hai 😊")


@Client.on_callback_query(filters.regex(r"^vj_buy_plan#"), group=0)
async def buy_plan_cb(client, query: CallbackQuery):
    plan_id = query.data.split("#")[1]
    plan    = next((p for p in PLANS if p["id"] == plan_id), None)
    if not plan:
        return await query.answer("Plan nahi mila!", show_alert=True)

    text = (
        f"<b>{plan['emoji']} {plan['name']} — {plan['price']} ({plan['duration']})</b>\n\n"
        f"📌 <b>Payment Steps:</b>\n"
        f"1️⃣ UPI ID: <code>arsadsaifi8272@ibl</code>\n"
        f"2️⃣ Amount: <b>{plan['price']}</b>\n"
        f"3️⃣ Neeche ka button dabao aur proof bhejo\n\n"
        f"⚠️ <i>Admin verify karega, thoda wait karo.</i>"
    )
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Screenshot / UTR Bhejo", callback_data=f"vj_submit_pay#{plan_id}")],
        [InlineKeyboardButton("⬅️ Plans Dekho", callback_data="vj_plan_pg#0")],
    ])
    try:
        await query.message.edit_caption(
            caption=text, reply_markup=btn, parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        try:
            await query.message.edit_text(
                text, reply_markup=btn, parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            await client.send_message(
                query.from_user.id, text, reply_markup=btn, parse_mode=enums.ParseMode.HTML
            )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^vj_submit_pay#"), group=0)
async def submit_pay_cb(client, query: CallbackQuery):
    plan_id = query.data.split("#")[1]
    plan    = next((p for p in PLANS if p["id"] == plan_id), None)
    if not plan:
        return await query.answer("Plan nahi mila!", show_alert=True)

    user_id = query.from_user.id
    PENDING_PAYMENT[user_id] = plan_id

    wait_text = (
        f"📸 <b>Payment Proof Bhejo</b>\n\n"
        f"Plan: <b>{plan['emoji']} {plan['name']} — {plan['price']}</b>\n\n"
        f"Is chat mein apna <b>Screenshot</b> ya <b>UTR Number</b> bhejo.\n"
        f"(Photo ya text — dono chalega)\n\n"
        f"<i>Seedha yahan bhejo, koi aur command mat likho abhi.</i>"
    )
    try:
        await client.send_message(user_id, wait_text, parse_mode=enums.ParseMode.HTML)
        await query.answer("Bot PM mein proof ka wait kar raha hai 📸", show_alert=True)
    except Exception:
        await query.answer(
            "Pehle bot ko PM mein /start karo, phir wapas aao!", show_alert=True
        )


@Client.on_message(
    filters.private & (filters.photo | filters.document | filters.text) & filters.incoming,
    group=10
)
async def receive_proof(client, message):
    user_id = message.from_user.id
    if user_id not in PENDING_PAYMENT:
        return
    if message.text and message.text.startswith("/"):
        return

    plan_id = PENDING_PAYMENT.pop(user_id)
    plan    = next((p for p in PLANS if p["id"] == plan_id), None)
    if not plan:
        return

    user       = message.from_user
    accept_cb  = f"vj_prem_accept#{user_id}#{plan['duration_code']}#{plan['name']}"
    reject_cb  = f"vj_prem_reject#{user_id}"
    action_btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Accept", callback_data=accept_cb),
        InlineKeyboardButton("❌ Reject", callback_data=reject_cb),
    ]])
    log_caption = (
        f"💰 <b>#PaymentProof</b>\n\n"
        f"👤 <b>User:</b> {user.mention} (<code>{user.id}</code>)\n"
        f"📦 <b>Plan:</b> {plan['emoji']} {plan['name']} — {plan['price']} ({plan['duration']})\n\n"
        f"<i>Accept ya Reject karo:</i>"
    )

    try:
        if message.photo or message.document:
            fwd = await message.forward(LOG_CHANNEL)
            await client.send_message(
                LOG_CHANNEL, log_caption,
                reply_markup=action_btn,
                reply_to_message_id=fwd.id,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            full = log_caption + f"\n\n📝 <b>UTR/Note:</b> <code>{message.text}</code>"
            await client.send_message(
                LOG_CHANNEL, full,
                reply_markup=action_btn,
                parse_mode=enums.ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Payment proof forward error: {e}")
        await message.reply_text(
            f"<b>❌ Forward mein error aaya. Admin ko directly contact karo:</b>\n{OWNER_LNK}",
            parse_mode=enums.ParseMode.HTML
        )
        return

    await message.reply_text(
        f"<b>✅ Proof admin ko bhej diya gaya!</b>\n\n"
        f"Plan: {plan['emoji']} <b>{plan['name']}</b>\n"
        f"⏳ Admin jaldi verify karega. /myplan se baad mein check karo.",
        parse_mode=enums.ParseMode.HTML
    )


@Client.on_callback_query(filters.regex(r"^vj_prem_accept#"), group=0)
async def prem_accept_cb(client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf Admin kar sakta hai!", show_alert=True)

    parts         = query.data.split("#", 3)
    user_id       = int(parts[1])
    duration_code = parts[2]

    seconds     = await get_seconds(duration_code)
    expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    await db.update_user({"id": user_id, "expiry_time": expiry_time, "has_free_trial": True})

    try:
        await query.message.edit_reply_markup(InlineKeyboardMarkup([[
            InlineKeyboardButton(
                f"✅ Accepted by {query.from_user.first_name}",
                callback_data="vj_plan_noop"
            )
        ]]))
    except Exception:
        pass

    accept_msg = (
        "👑 ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ 👑\n\n"
        "🙏 ʙᴀʜᴜᴛ-ʙᴀʜᴜᴛ ꜱʜᴜᴋʀɪʏᴀ! Aapki payment confirm ho gayi hai.\n\n"
        "🎬 ᴀʙ ᴍᴀᴢᴀ ʜɪ ᴍᴀᴢᴀ:\n"
        "●⚡ ᴅɪʀᴇᴄᴛ ꜰɪʟᴇꜱ & ɴᴏ ᴀᴅꜱ\n"
        "● 🚀 ᴜɴʟɪᴍɪᴛᴇᴅ ꜱᴘᴇᴇᴅ ᴀᴜʀ ᴀᴄᴄᴇꜱꜱ\n\n"
        "ᴠᴀʟɪᴅɪᴛʏ ᴄʜᴇᴄᴋ ᴋᴀʀᴇɪɴ: /myplan\n\n"
        "🎁 ꜰʀᴇᴇ ᴘʀᴇᴍɪᴜᴍ ᴡɪɴ ᴋᴀʀᴏ!\n"
        "Hamare channel @asbhai_bsr par har 1 taarikh ko FREE Premium ka Giveaway hota hai!\n"
        "Join karke ek 🔥 Reaction de den aur doston ko bhi batayen!\n\n"
        "Happy Streaming! 🎉"
    )
    try:
        await client.send_message(user_id, accept_msg)
    except Exception as e:
        logger.error(f"Accept notify error: {e}")

    await query.answer(f"✅ Premium activated for {user_id}!", show_alert=True)


@Client.on_callback_query(filters.regex(r"^vj_prem_reject#"), group=0)
async def prem_reject_cb(client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf Admin kar sakta hai!", show_alert=True)

    user_id = int(query.data.split("#")[1])

    try:
        await query.message.edit_reply_markup(InlineKeyboardMarkup([[
            InlineKeyboardButton(
                f"❌ Rejected by {query.from_user.first_name}",
                callback_data="vj_plan_noop"
            )
        ]]))
    except Exception:
        pass

    reject_msg = (
        "❌ <b>Payment Reject Ho Gaya</b>\n\n"
        "Aapka payment verify nahi ho saka.\n\n"
        "<b>Possible reasons:</b>\n"
        "• Screenshot clear nahi tha\n"
        "• UTR invalid tha\n"
        "• Amount match nahi kiya\n\n"
        f"Dobara try karo ya Admin se contact karo:\n{OWNER_LNK}"
    )
    try:
        await client.send_message(user_id, reject_msg, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Reject notify error: {e}")

    await query.answer("❌ Rejected and user notified.", show_alert=True)
