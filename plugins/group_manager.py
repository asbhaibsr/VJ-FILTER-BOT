# Group Manager Plugin
# /mygroups  — Paginated list of all groups bot is in (10 per page)
#              Inactive groups auto-cleanup + join button per group
# Owner joins any group → Royal welcome message

import asyncio, logging
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
)
from database.users_chats_db import db
from info import ADMINS, LOG_CHANNEL, SUPPORT_CHAT, OWNER_LNK, CHNL_LNK
from utils import temp

logger = logging.getLogger(__name__)

PAGE_SIZE = 10   # Groups per page

# ── in-memory cache (refreshed on each /mygroups call) ──────────
_GROUPS_CACHE = {}   # request_msg_id -> [{"id": ..., "title": ...}, ...]


def _build_page(groups: list, page: int, total_active: int, removed: int):
    """Build text + markup for one page"""
    start  = page * PAGE_SIZE
    end    = start + PAGE_SIZE
    chunk  = groups[start:end]
    total  = len(groups)
    pages  = (total + PAGE_SIZE - 1) // PAGE_SIZE or 1

    text = (
        f"<b>📋 Bot Ke Groups  —  Page {page+1}/{pages}</b>\n\n"
        f"✅ Active: <b>{total_active}</b>  |  "
        f"🗑 Removed: <b>{removed}</b>\n\n"
    )

    buttons = []
    for g in chunk:
        gid   = g["id"]
        title = g["title"][:28] + "…" if len(g["title"]) > 28 else g["title"]
        # Invite link button — user clicks to open group
        try:
            invite_url = f"https://t.me/c/{str(gid).replace('-100', '')}"
        except Exception:
            invite_url = f"https://t.me/c/{gid}"
        buttons.append([
            InlineKeyboardButton(f"🏘 {title}", url=invite_url)
        ])

    # Pagination row
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"mg_page#{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{pages}", callback_data="mg_noop"))
    if end < total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"mg_page#{page+1}"))

    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="mg_refresh"),
                    InlineKeyboardButton("❌ Close",   callback_data="close_data")])

    return text, InlineKeyboardMarkup(buttons)


async def _fetch_groups(bot) -> tuple:
    """
    Fetch all groups from DB, verify each one (bot still member?),
    remove dead ones, return (active_list, removed_count)
    """
    active_list  = []
    inactive_ids = []

    try:
        all_chats = await db.grp.find({}).to_list(length=None)
    except Exception:
        all_chats = []
        async for c in db.grp.find({}):
            all_chats.append(c)

    for chat in all_chats:
        chat_id = chat.get("id")
        if not chat_id:
            continue
        title = chat.get("title", "Unknown Group")
        try:
            chat_obj = await bot.get_chat(int(chat_id))
            # Update title in DB if changed
            if chat_obj.title and chat_obj.title != title:
                await db.grp.update_one({"id": chat_id}, {"$set": {"title": chat_obj.title}})
                title = chat_obj.title
            active_list.append({"id": chat_id, "title": title})
        except Exception:
            inactive_ids.append(chat_id)

    # Remove dead groups from DB
    for cid in inactive_ids:
        try:
            await db.grp.delete_one({"id": cid})
        except Exception:
            pass

    return active_list, len(inactive_ids)


# ── /mygroups command ────────────────────────────────────────────
@Client.on_message(filters.command(["mygroups", "groups"]) & filters.user(ADMINS), group=-1)
async def mygroups_cmd(bot, message: Message):
    sts = await message.reply_text(
        "<b>⏳ Saare groups check ho rahe hain, thoda wait karo...\n"
        "<i>(Inactive groups automatically remove honge)</i></b>",
        parse_mode=enums.ParseMode.HTML
    )

    try:
        active_list, removed = await _fetch_groups(bot)
    except Exception as e:
        return await sts.edit_text(f"<b>❌ Error: {e}</b>", parse_mode=enums.ParseMode.HTML)

    if not active_list:
        return await sts.edit_text(
            f"<b>😶 Bot kisi bhi group mein nahi hai abhi!\n\n"
            f"🗑 {removed} inactive records delete kiye.</b>",
            parse_mode=enums.ParseMode.HTML
        )

    # Cache the list against this status message id
    _GROUPS_CACHE[sts.id] = {
        "groups":  active_list,
        "removed": removed,
        "owner":   message.from_user.id
    }

    text, markup = _build_page(active_list, 0, len(active_list), removed)
    await sts.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


# ── Pagination callback ──────────────────────────────────────────
@Client.on_callback_query(filters.regex(r"^mg_page#"))
async def mg_page_cb(bot, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf admin dekh sakta hai!", show_alert=True)

    page = int(query.data.split("#")[1])
    msg  = query.message

    # Find cache
    cache = _GROUPS_CACHE.get(msg.id)
    if not cache:
        # Re-fetch if cache expired
        await query.answer("Cache expired, refresh kar raha hoon...", show_alert=False)
        try:
            active_list, removed = await _fetch_groups(bot)
            _GROUPS_CACHE[msg.id] = {"groups": active_list, "removed": removed, "owner": query.from_user.id}
            cache = _GROUPS_CACHE[msg.id]
        except Exception as e:
            return await query.answer(f"Error: {e}", show_alert=True)

    groups  = cache["groups"]
    removed = cache["removed"]

    text, markup = _build_page(groups, page, len(groups), removed)
    try:
        await msg.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass
    await query.answer()


# ── Refresh callback ─────────────────────────────────────────────
@Client.on_callback_query(filters.regex("^mg_refresh$"))
async def mg_refresh_cb(bot, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("Sirf admin!", show_alert=True)

    await query.answer("🔄 Refresh ho raha hai...", show_alert=False)
    try:
        await query.message.edit_text(
            "<b>⏳ Groups check ho rahe hain...</b>",
            parse_mode=enums.ParseMode.HTML
        )
        active_list, removed = await _fetch_groups(bot)
        _GROUPS_CACHE[query.message.id] = {
            "groups":  active_list,
            "removed": removed,
            "owner":   query.from_user.id
        }
        if not active_list:
            return await query.message.edit_text(
                f"<b>😶 Bot kisi group mein nahi hai!\n🗑 {removed} removed.</b>",
                parse_mode=enums.ParseMode.HTML
            )
        text, markup = _build_page(active_list, 0, len(active_list), removed)
        await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await query.answer(f"Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^mg_noop$"))
async def mg_noop_cb(bot, query: CallbackQuery):
    await query.answer("Ye page number hai 😊")


# ════════════════════════════════════════════════════════════════
#   OWNER ROYAL WELCOME  — Jab owner kisi group mein aaye
# ════════════════════════════════════════════════════════════════

ROYAL_MESSAGES = [
    (
        "👑 <b>ᴀᴀ ɢᴀʏᴇ ʜᴜᴢᴏᴏʀ!</b> 👑\n\n"
        "🎺 <b>Dhol bajao! Shehnai bajao!</b>\n"
        "Hamare pyaare <b>Malik</b> {mention} ne is group mein\n"
        "apne qadam rakkhe hain! 🦁\n\n"
        "🌟 Ye woh shakhs hai jisne ye bot banaya,\n"
        "jisne raat ko jaag ke code likha,\n"
        "aur aap sab ke liye ye sab kuch kiya! 💪\n\n"
        "🙏 <b>Tashreef laane ka shukriya, Baadshaah!</b>\n"
        "Aapki khidmat mein hamesha tayyar hoon. 🫡"
    ),
    (
        "🚨 <b>ALERT! ALERT! ALERT!</b> 🚨\n\n"
        "⚡ Bijli aa gayi! Mehfil roshaan ho gayi!\n\n"
        "👑 <b>{mention}</b> — humara <b>Baadshaah</b>\n"
        "is group mein padhaare hain!\n\n"
        "🎖 Ye woh insaan hai jo:\n"
        "• Is bot ke <b>Creator</b> hain 🛠\n"
        "• Sabke kaam aane wale <b>Asli Malik</b> hain 🏆\n"
        "• Jinka hukm sirf bot hi nahi,\n"
        "  ye pura server maanta hai! 💻\n\n"
        "🔱 <b>Jai ho Huzoor! Swagat hai!</b> 🔱"
    ),
    (
        "🎊 <b>Khush-Aamdeed! Khush-Aamdeed!</b> 🎊\n\n"
        "🌹 Is group ka sabse khaas mehmaan aa gaya!\n\n"
        "💎 <b>{mention}</b> — Jinhe hum pyaar se\n"
        "<b>\"Bot Ka Baap\"</b> kehte hain 😄👑\n\n"
        "🙌 Ye wo insaan hai jisne:\n"
        "• Hamare liye ye sab build kiya\n"
        "• Kabhi bina ruke kaam kiya\n"
        "• Aur sab free mein diya! 🤍\n\n"
        "🫅 <b>Huzoor ka dil se Swagat hai!</b>\n"
        "Aapka ye group hamesha aapka intezaar karta hai! 🕊"
    ),
]

import random

@Client.on_message(filters.new_chat_members & filters.group, group=2)
async def owner_royal_welcome(bot, message: Message):
    """Jab owner kisi group mein aaye, royal welcome karo"""
    try:
        joining_ids = [u.id for u in message.new_chat_members]

        # Check if owner/admin joined
        owner_user = None
        for u in message.new_chat_members:
            if u.id in ADMINS:
                owner_user = u
                break

        if not owner_user:
            return  # Normal user, skip karo

        # Bot khud join hua to skip (wo alag handler handle karta hai)
        if owner_user.id == temp.ME:
            return

        mention = owner_user.mention

        # Random royal message choose karo
        royal_text = random.choice(ROYAL_MESSAGES).format(mention=mention)

        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton("👑 Malik Ka Channel", url=OWNER_LNK),
            InlineKeyboardButton("🤖 Bot Updates",      url=CHNL_LNK)
        ]])

        await message.reply_text(
            royal_text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )

    except Exception as e:
        logger.error(f"Owner royal welcome error: {e}")
