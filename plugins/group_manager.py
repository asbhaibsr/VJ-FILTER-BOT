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
    for i, g in enumerate(chunk, start=start+1):
        gid     = g["id"]
        title   = g["title"]
        title   = title[:26] + "…" if len(title) > 26 else title
        members = g.get("members", 0)
        link    = g.get("link")   # Real invite link or None
        label   = f"🏘 {i}. {title}"
        if members:
            label += f" ({members})"
        if link:
            # Has real invite link - show clickable button
            buttons.append([InlineKeyboardButton(label, url=link)])
        else:
            # No invite link available - show as non-clickable info
            buttons.append([InlineKeyboardButton(f"🔒 {i}. {title} (no link)", callback_data="mg_noop")])

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
    generate real invite link via export_chat_invite_link,
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

    seen_ids = set()   # Duplicate ID tracker
    for chat in all_chats:
        chat_id = chat.get("id")
        if not chat_id:
            continue
        # Skip duplicate entries (same group added multiple times)
        norm_id = int(chat_id)
        if norm_id in seen_ids:
            # Remove duplicate from DB
            try:
                await db.grp.delete_one({"_id": chat.get("_id")})
            except Exception:
                pass
            continue
        seen_ids.add(norm_id)
        title = chat.get("title", "Unknown Group")
        try:
            chat_obj = await bot.get_chat(int(chat_id))
            # Update title in DB if changed
            if chat_obj.title and chat_obj.title != title:
                await db.grp.update_one({"id": chat_id}, {"$set": {"title": chat_obj.title}})
                title = chat_obj.title

            # ── Real invite link banao ─────────────────────
            invite_link = None

            # 1st try: existing invite_link from chat object
            if hasattr(chat_obj, "invite_link") and chat_obj.invite_link:
                invite_link = chat_obj.invite_link

            # 2nd try: export new invite link (bot admin hona chahiye)
            if not invite_link:
                try:
                    invite_link = await bot.export_chat_invite_link(int(chat_id))
                except Exception:
                    pass

            # 3rd try: public username
            if not invite_link:
                try:
                    if hasattr(chat_obj, "username") and chat_obj.username:
                        invite_link = f"https://t.me/{chat_obj.username}"
                except Exception:
                    pass

            # 4th fallback: ONLY use t.me/c/ if all above failed
            # This URL requires user to already be a member - mark it
            if not invite_link:
                gid_str = str(chat_id)
                if gid_str.startswith("-100"):
                    clean_id = gid_str[4:]
                elif gid_str.startswith("-"):
                    clean_id = gid_str[1:]
                else:
                    clean_id = gid_str
                invite_link = f"https://t.me/c/{clean_id}"
                # Flag that this is NOT a real invite link
                invite_link = None   # Skip - no valid link available

            active_list.append({
                "id":     chat_id,
                "title":  title,
                "link":   invite_link,
                "members": getattr(chat_obj, "members_count", 0) or 0
            })
        except Exception:
            inactive_ids.append(chat_id)

    # Remove dead/left groups from DB
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


# Owner royal welcome is handled in p_ttishow.py → save_group handler
