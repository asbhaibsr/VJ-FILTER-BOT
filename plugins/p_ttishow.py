# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os, string, logging, random, asyncio, time, datetime, re, sys, json, base64, io
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_OK = True
except ImportError:
    PIL_OK = False
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
from database.ia_filterdb import col, sec_col, get_file_details, unpack_new_file_id, get_bad_files, db as vjdb, sec_db
from database.users_chats_db import db, delete_all_referal_users, get_referal_users_count, get_referal_all_users, referal_add_user
from database.join_reqs import JoinReqs
from info import *
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong, PeerIdInvalid
from utils import get_settings, pub_is_subscribed, get_size, is_subscribed, save_group_settings, temp, verify_user, check_token, check_verification, get_token, get_shortlink, get_tutorial, get_seconds
from database.connections_mdb import active_connection, mydb


# ══════════════════════════════════════════════════════════════
#   WELCOME CARD GENERATOR (PIL)
# ══════════════════════════════════════════════════════════════
_FONT_PATH = "/usr/share/fonts/truetype/liberation/"

async def _make_welcome_card(bot, user_id, first_name, group_title, member_count=0, is_owner=False):
    """PIL se dynamic welcome image banao"""
    if not PIL_OK:
        return None
    try:
        W, H = 1280, 640
        AV_X, AV_Y, AV_SIZE = 90, (H-330)//2, 330

        # Background gradient
        if is_owner:
            c1, c2 = (45, 25, 10), (80, 45, 10)       # Gold/dark
            border_col = (255, 190, 30)
            title_col  = (255, 215, 0)
            name_col   = (255, 235, 100)
            sub_col    = (245, 225, 170)
            badge_fill = (160, 100, 10)
            av_border  = (255, 190, 30)
        else:
            c1, c2 = (28, 18, 72), (55, 35, 110)       # Purple
            border_col = (140, 110, 240)
            title_col  = (255, 255, 255)
            name_col   = (180, 150, 255)
            sub_col    = (210, 200, 240)
            badge_fill = (100, 80, 200)
            av_border  = (150, 120, 255)

        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)
        for y in range(H):
            t = y / H
            r = int(c1[0]*(1-t)+c2[0]*t)
            g = int(c1[1]*(1-t)+c2[1]*t)
            b = int(c1[2]*(1-t)+c2[2]*t)
            draw.line([(0,y),(W,y)], fill=(r,g,b))

        # Border
        draw.rounded_rectangle([28,28,W-28,H-28], radius=40, outline=border_col, width=3)

        # Fonts
        try:
            f_big   = ImageFont.truetype(_FONT_PATH+"LiberationSans-Bold.ttf",    85 if not is_owner else 78)
            f_name  = ImageFont.truetype(_FONT_PATH+"LiberationSans-Bold.ttf",    56)
            f_sub   = ImageFont.truetype(_FONT_PATH+"LiberationSans-Regular.ttf", 38)
            f_badge = ImageFont.truetype(_FONT_PATH+"LiberationSans-Bold.ttf",    28)
        except Exception:
            f_big = f_name = f_sub = f_badge = ImageFont.load_default()

        # Avatar
        av_img = None
        try:
            photos = await bot.get_profile_photos(user_id, limit=1)
            if photos.total_count > 0:
                av_buf = io.BytesIO()
                await bot.download_media(photos[0].file_id, file=av_buf)
                av_buf.seek(0)
                src = Image.open(av_buf).convert("RGBA").resize((AV_SIZE, AV_SIZE))
                mask = Image.new("L", (AV_SIZE, AV_SIZE), 0)
                ImageDraw.Draw(mask).ellipse([0,0,AV_SIZE-1,AV_SIZE-1], fill=255)
                av_img = Image.new("RGBA", (AV_SIZE+10, AV_SIZE+10), (0,0,0,0))
                # Border ring
                ImageDraw.Draw(av_img).ellipse([0,0,AV_SIZE+9,AV_SIZE+9], fill=av_border+(255,))
                av_inner = Image.new("RGBA", (AV_SIZE, AV_SIZE), (0,0,0,0))
                av_inner.paste(src, (0,0), mask)
                av_img.paste(av_inner, (5,5), mask)
        except Exception:
            pass

        if av_img is None:
            # Initials fallback
            av_img = Image.new("RGBA", (AV_SIZE+10, AV_SIZE+10), (0,0,0,0))
            ImageDraw.Draw(av_img).ellipse([0,0,AV_SIZE+9,AV_SIZE+9], fill=av_border+(255,))
            ImageDraw.Draw(av_img).ellipse([5,5,AV_SIZE+4,AV_SIZE+4], fill=(70,50,160,255) if not is_owner else (140,90,10,255))
            try:
                f_init = ImageFont.truetype(_FONT_PATH+"LiberationSans-Bold.ttf", 130)
            except Exception:
                f_init = ImageFont.load_default()
            initials = (first_name[0] if first_name else "?").upper()
            bbox = f_init.getbbox(initials)
            ix = (AV_SIZE+10-(bbox[2]-bbox[0]))//2
            iy = (AV_SIZE+10-(bbox[3]-bbox[1]))//2 - 5
            ImageDraw.Draw(av_img).text((ix, iy), initials, fill=(255,255,255,255), font=f_init)

        img.paste(av_img, (AV_X, AV_Y), av_img)

        # Text
        tx = AV_X + AV_SIZE + 55
        ty = 80

        if is_owner:
            draw.text((tx, ty), "👑 AA GAYE HUZOOR! 👑", fill=title_col, font=f_sub)
            ty += 55
            nm = first_name[:20]
            draw.text((tx, ty), nm, fill=name_col, font=f_big)
            ty += 100
            draw.text((tx, ty), (group_title[:30] if len(group_title)<=30 else group_title[:29]+"…"), fill=sub_col, font=f_name)
            ty += 68
            draw.text((tx, ty), "Bot Ka Maalik aa gaya! 🔥", fill=(255,200,80), font=f_sub)
            ty += 52
        else:
            draw.text((tx, ty), "WELCOME", fill=title_col, font=f_big)
            ty += 100
            nm = first_name[:22]
            draw.text((tx, ty), nm, fill=name_col, font=f_name)
            ty += 70
            draw.text((tx, ty), "to "+( group_title[:28] if len(group_title)<=28 else group_title[:27]+"…"), fill=sub_col, font=f_sub)
            ty += 52
            draw.text((tx, ty), "Bot is now watching over this chat 👁", fill=(160,155,200), font=ImageFont.truetype(_FONT_PATH+"LiberationSans-Regular.ttf", 30) if PIL_OK else f_badge)
            ty += 50

        # Members badge
        if member_count:
            badge_txt = f"👥  {member_count:,} Members"
            try:
                bbox = f_badge.getbbox(badge_txt)
                bw = bbox[2]-bbox[0]+40
                bh = bbox[3]-bbox[1]+18
            except Exception:
                bw, bh = 250, 44
            draw.rounded_rectangle([tx, ty, tx+bw, ty+bh], radius=16,
                                    fill=badge_fill, outline=border_col, width=2)
            draw.text((tx+15, ty+9), badge_txt, fill=(255,255,255), font=f_badge)

        buf = io.BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        logging.getLogger(__name__).error(f"Welcome card error: {e}")
        return None


@Client.on_message(filters.new_chat_members & filters.group)
async def save_group(bot, message):
    r_j_check = [u.id for u in message.new_chat_members]
    if temp.ME in r_j_check:
        if not await db.get_chat(message.chat.id):
            total=await bot.get_chat_members_count(message.chat.id)
            r_j = message.from_user.mention if message.from_user else "Anonymous" 
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, r_j))       
            await db.add_chat(message.chat.id, message.chat.title)
        if message.chat.id in temp.BANNED_CHATS:
            # Inspired from a boat of a banana tree
            buttons = [[
                InlineKeyboardButton('Support', url=f'https://t.me/{SUPPORT_CHAT}')
            ]]
            reply_markup=InlineKeyboardMarkup(buttons)
            k = await message.reply(
                text='<b>CHAT NOT ALLOWED 🐞\n\nMy admins has restricted me from working here ! If you want to know more about it contact support..</b>',
                reply_markup=reply_markup,
            )
            try:
                await k.pin()
            except:
                pass
            await bot.leave_chat(message.chat.id)
            return
        buttons = [[
            InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
            InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
        ],[
            InlineKeyboardButton("Bᴏᴛ Oᴡɴᴇʀ", url=OWNER_LNK)
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await message.reply_text(
            text=f"<b>Thankyou For Adding Me In {message.chat.title} ❣️\n\nIf you have any questions & doubts about using me contact support.</b>",
            reply_markup=reply_markup
        )
        # Agar owner bhi saath mein add hua to royal welcome do
        import random as _rnd2
        for _u in message.new_chat_members:
            if _u.id in ADMINS and _u.id != temp.ME:
                _rmsgs = [
                    (
                        "👑 <b>ᴀᴀ ɢᴀʏᴇ ʜᴜᴢᴏᴏʀ!</b> 👑\n\n"
                        "🎺 <b>Dhol bajao! Shehnai bajao!</b>\n"
                        f"Hamare pyaare <b>Malik</b> {_u.mention} ne\n"
                        f"<b>{message.chat.title}</b> mein qadam rakkhe! 🦁\n\n"
                        "🌟 Ye woh shakhs hai jisne ye bot banaya,\n"
                        "raat jaag ke code likha,\n"
                        "aur sab ke liye free kiya! 💪\n\n"
                        "🙏 <b>Tashreef laane ka shukriya, Baadshaah!</b> 🫡"
                    ),
                    (
                        "🚨 <b>ALERT! ALERT! ALERT!</b> 🚨\n\n"
                        "⚡ Bijli aa gayi! Mehfil roshaan ho gayi!\n\n"
                        f"👑 <b>{_u.mention}</b> — humara <b>Baadshaah</b>\n"
                        f"<b>{message.chat.title}</b> mein padhaare hain!\n\n"
                        "🎖 Ye woh insaan hai jo:\n"
                        "• Is bot ke <b>Creator</b> hain 🛠\n"
                        "• Sabke kaam aane wale <b>Asli Malik</b> hain 🏆\n"
                        "• Jinka hukm pura server maanta hai! 💻\n\n"
                        "🔱 <b>Jai ho Huzoor! Swagat hai!</b> 🔱"
                    ),
                    (
                        "🎊 <b>Khush-Aamdeed! Khush-Aamdeed!</b> 🎊\n\n"
                        "🌹 Is group ka sabse khaas mehmaan aa gaya!\n\n"
                        f"💎 <b>{_u.mention}</b>\n"
                        "Jinhe pyaar se <b>'Bot Ka Baap'</b> kehte hain 😄👑\n\n"
                        "🙌 Ye wo insaan hai jisne:\n"
                        "• Sab kuch build kiya aur free diya! 🤍\n"
                        "• Kabhi bina ruke kaam kiya!\n\n"
                        "🫅 <b>Huzoor ka dil se Swagat hai!</b> 🕊"
                    ),
                    (
                        "🏆 <b>VIP ENTRY!</b> 🏆\n\n"
                        f"✨ Koi aam insaan nahi —\n"
                        f"<b>{_u.mention}</b> aa gaye hain! 👑\n\n"
                        f"🏘 <b>{message.chat.title}</b> ko aaj\n"
                        "apna maalik wapis mila hai! 💫\n\n"
                        "🎯 Ye wahi hain jo:\n"
                        "• Sote nahi, code likhte hain 🌙\n"
                        "• Sikhte nahi, sikhate hain 🎓\n"
                        "• Lete nahi, dete hain! 🎁\n\n"
                        "💐 <b>Huzoor, Aadab! Khush rehein hamesha!</b>"
                    ),
                ]
                _btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("👑 Malik Ka Channel", url=OWNER_LNK),
                    InlineKeyboardButton("🤖 Updates", url=CHNL_LNK)
                ]])
                try:
                    try:
                        _mc2 = await bot.get_chat_members_count(message.chat.id)
                    except Exception:
                        _mc2 = 0
                    _oc = await _make_welcome_card(
                        bot, _u.id, _u.first_name or "Owner",
                        message.chat.title, _mc2, is_owner=True
                    )
                    _royal_txt = _rnd2.choice(_rmsgs)
                    if _oc:
                        await message.reply_photo(photo=_oc, caption=_royal_txt, reply_markup=_btn, parse_mode=enums.ParseMode.HTML)
                    else:
                        await message.reply_text(_royal_txt, reply_markup=_btn, parse_mode=enums.ParseMode.HTML)
                except Exception:
                    pass
    else:
        settings = await get_settings(message.chat.id)
        for u in message.new_chat_members:
            # ── Owner/Admin royal welcome ───────────────────
            if u.id in ADMINS:
                import random as _random
                royal_msgs = [
                    (
                        "👑 <b>ᴀᴀ ɢᴀʏᴇ ʜᴜᴢᴏᴏʀ!</b> 👑\n\n"
                        "🎺 <b>Dhol bajao! Shehnai bajao!</b>\n"
                        f"Hamare pyaare <b>Malik</b> {u.mention} ne\n"
                        f"<b>{message.chat.title}</b> mein qadam rakkhe! 🦁\n\n"
                        "🌟 Ye woh shakhs hai jisne ye bot banaya,\n"
                        "raat jaag ke code likha,\n"
                        "aur sab ke liye free kiya! 💪\n\n"
                        "🙏 <b>Tashreef laane ka shukriya, Baadshaah!</b> 🫡"
                    ),
                    (
                        "🚨 <b>ALERT! ALERT! ALERT!</b> 🚨\n\n"
                        "⚡ Bijli aa gayi! Mehfil roshaan ho gayi!\n\n"
                        f"👑 <b>{u.mention}</b> — humara <b>Baadshaah</b>\n"
                        f"<b>{message.chat.title}</b> mein padhaare hain!\n\n"
                        "🎖 Ye woh insaan hai jo:\n"
                        "• Is bot ke <b>Creator</b> hain 🛠\n"
                        "• Sabke kaam aane wale <b>Asli Malik</b> hain 🏆\n"
                        "• Jinka hukm pura server maanta hai! 💻\n\n"
                        "🔱 <b>Jai ho Huzoor! Swagat hai!</b> 🔱"
                    ),
                    (
                        "🎊 <b>Khush-Aamdeed! Khush-Aamdeed!</b> 🎊\n\n"
                        "🌹 Is group ka sabse khaas mehmaan aa gaya!\n\n"
                        f"💎 <b>{u.mention}</b>\n"
                        "Jinhe pyaar se <b>'Bot Ka Baap'</b> kehte hain 😄👑\n\n"
                        "🙌 Ye wo insaan hai jisne:\n"
                        "• Sab kuch build kiya aur free diya! 🤍\n"
                        "• Kabhi bina ruke kaam kiya!\n\n"
                        "🫅 <b>Huzoor ka dil se Swagat hai!</b> 🕊"
                    ),
                    (
                        "🏆 <b>VIP ENTRY!</b> 🏆\n\n"
                        f"✨ Koi aam insaan nahi —\n"
                        f"<b>{u.mention}</b> aa gaye hain! 👑\n\n"
                        f"🏘 <b>{message.chat.title}</b> ko aaj\n"
                        "apna maalik wapis mila hai! 💫\n\n"
                        "🎯 Ye wahi hain jo:\n"
                        "• Sote nahi, code likhte hain 🌙\n"
                        "• Sikhte nahi, sikhate hain 🎓\n"
                        "• Lete nahi, dete hain! 🎁\n\n"
                        "💐 <b>Huzoor, Aadab! Khush rehein hamesha!</b>"
                    ),
                    (
                        "🌟 <b>ROYAL ARRIVAL!</b> 🌟\n\n"
                        f"🎭 Is mehfil mein aaj ek khaas shaks aaya,\n"
                        f"Jinke naam se ye bot jaana jaata hai!\n\n"
                        f"🔥 <b>{u.mention}</b>\n"
                        f"<b>{message.chat.title}</b> mein aapka\n"
                        "tah-e-dil se Istaqbal hai! 🤝\n\n"
                        "📌 Fun Fact:\n"
                        "• Ye bot unka banaya hua hai 🛠\n"
                        "• Ye server unka chalaya hua hai ☁️\n"
                        "• Ye group unka pataya hua hai 😄\n\n"
                        "🎁 <b>Huzoor ko hazaar salaam!</b> 🫅"
                    ),
                ]
                royal_text = _random.choice(royal_msgs)
                royal_btn  = InlineKeyboardMarkup([[
                    InlineKeyboardButton("👑 Malik Ka Channel", url=OWNER_LNK),
                    InlineKeyboardButton("🤖 Updates",          url=CHNL_LNK)
                ]])
                try:
                    try:
                        member_count = await bot.get_chat_members_count(message.chat.id)
                    except Exception:
                        member_count = 0
                    owner_card = await _make_welcome_card(
                        bot, u.id, u.first_name or "Owner",
                        message.chat.title, member_count, is_owner=True
                    )
                    if owner_card:
                        await message.reply_photo(
                            photo=owner_card,
                            caption=royal_text,
                            reply_markup=royal_btn,
                            parse_mode=enums.ParseMode.HTML
                        )
                    else:
                        await message.reply_text(
                            royal_text,
                            reply_markup=royal_btn,
                            parse_mode=enums.ParseMode.HTML
                        )
                except Exception as _e:
                    logging.getLogger(__name__).error(f"Owner welcome error: {_e}")
                    try:
                        await message.reply_text(royal_text, reply_markup=royal_btn, parse_mode=enums.ParseMode.HTML)
                    except Exception:
                        pass
                continue   # Normal welcome skip karo admin ke liye

            # ── Normal user welcome ─────────────────────────
            if settings["welcome"]:
                if (temp.MELCOW).get('welcome') is not None:
                    try:
                        await (temp.MELCOW['welcome']).delete()
                    except:
                        pass
                button = [[
                    InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                    InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                ],[
                    InlineKeyboardButton("📥 How to Download", url="https://t.me/asbhai_bsr/671"),
                    InlineKeyboardButton("Bᴏᴛ Oᴡɴᴇʀ", url=OWNER_LNK)
                ]]
                try:
                    member_count = await bot.get_chat_members_count(message.chat.id)
                except Exception:
                    member_count = 0
                card = await _make_welcome_card(
                    bot, u.id, u.first_name or "User",
                    message.chat.title, member_count, is_owner=False
                )
                if card:
                    temp.MELCOW['welcome'] = await message.reply_photo(
                        photo=card,
                        caption=script.MELCOW_ENG.format(u.mention, message.chat.title),
                        reply_markup=InlineKeyboardMarkup(button),
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    # PIL fail hone pe text fallback
                    temp.MELCOW['welcome'] = await message.reply_text(
                        text=script.MELCOW_ENG.format(u.mention, message.chat.title),
                        reply_markup=InlineKeyboardMarkup(button),
                        parse_mode=enums.ParseMode.HTML
                    )
        if settings.get("auto_delete") and (temp.MELCOW).get('welcome'):
            await asyncio.sleep(600)
            try:
                await (temp.MELCOW['welcome']).delete()
            except Exception:
                pass

@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_a_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        chat = chat
    try:
        buttons = [[
            InlineKeyboardButton('Support Group',url=f'https://t.me/{SUPPORT_CHAT}'),
            InlineKeyboardButton("Bᴏᴛ Oᴡɴᴇʀ", url=OWNER_LNK)
        ],[
            InlineKeyboardButton('Use Me Here', url=f'https://t.me/{SUPPORT_CHAT}')
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat,
            text='<b>Hello Friends, \nMy admin has told me to leave from group, so i go! If you wanna add me again contact my Support Group or My Owner</b>',
            reply_markup=reply_markup,
        )

        await bot.leave_chat(chat)
        await message.reply(f"left the chat `{chat}`")
    except Exception as e:
        await message.reply(f'Error - {e}')

@Client.on_message(filters.command('disable') & filters.user(ADMINS))
async def disable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    cha_t = await db.get_chat(int(chat_))
    if not cha_t:
        return await message.reply("Chat Not Found In DB")
    if cha_t['is_disabled']:
        return await message.reply(f"This chat is already disabled:\nReason-<code> {cha_t['reason']} </code>")
    await db.disable_chat(int(chat_), reason)
    temp.BANNED_CHATS.append(int(chat_))
    await message.reply('Chat Successfully Disabled')
    try:
        buttons = [[
            InlineKeyboardButton('Support', url=f'https://t.me/{SUPPORT_CHAT}')
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat_, 
            text=f'<b>Hello Friends, \nMy admin has told me to leave from group so i go! If you wanna add me again contact my support group.</b> \nReason : <code>{reason}</code>',
            reply_markup=reply_markup)
        await bot.leave_chat(chat_)
    except Exception as e:
        await message.reply(f"Error - {e}")

@Client.on_message(filters.command('enable') & filters.user(ADMINS))
async def re_enable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    sts = await db.get_chat(int(chat))
    if not sts:
        return await message.reply("Chat Not Found In DB !")
    if not sts.get('is_disabled'):
        return await message.reply('This chat is not yet disabled.')
    await db.re_enable_chat(int(chat_))
    temp.BANNED_CHATS.remove(int(chat_))
    await message.reply("Chat Successfully re-enabled")

@Client.on_message(filters.command('stats') & filters.incoming)
async def get_ststs(bot, message):
    rju = await message.reply('<b>⏳ Stats fetch ho rahi hain...</b>', parse_mode=enums.ParseMode.HTML)
    try:
        total_users  = await db.total_users_count()
        totl_chats   = await db.total_chat_count()
        premium_cnt  = await db.all_premium_users()
        filesp       = col.count_documents({})
        stats        = vjdb.command('dbStats')
        used_dbSize  = (stats['dataSize']/(1024*1024)) + (stats['indexSize']/(1024*1024))
        free_dbSize  = 512 - used_dbSize

        # Top 3 searches
        try:
            top_s = await db.get_top_searches(3)
            if top_s:
                top_lines = " | ".join([f"{d['query']} ({d['count']}x)" for d in top_s])
            else:
                top_lines = "No data yet"
        except Exception:
            top_lines = "N/A"

        # Redeem code summary
        try:
            codes_info = await db.get_all_codes_count()
            codes_str  = f"Active: {codes_info['active']} | Used: {codes_info['used']}"
        except Exception:
            codes_str = "N/A"

        base_stats = (
            "<b>📊 Bot Statistics</b>\n\n"
            f"👥 <b>Total Users:</b> <code>{total_users}</code>\n"
            f"🏘 <b>Total Groups:</b> <code>{totl_chats}</code>\n"
            f"💎 <b>Premium Users:</b> <code>{premium_cnt}</code>\n"
            f"🎬 <b>Total Files:</b> <code>{filesp}</code>\n\n"
            f"🔑 <b>Redeem Codes:</b> {codes_str}\n"
            f"🔥 <b>Top Searches:</b> {top_lines}\n\n"
            f"🗄 <b>DB Used:</b> <code>{round(used_dbSize, 2)} MB</code>\n"
            f"💾 <b>DB Free:</b> <code>{round(free_dbSize, 2)} MB</code>"
        )

        if MULTIPLE_DATABASE == False:
            await rju.edit(base_stats, parse_mode=enums.ParseMode.HTML)
            return

        totalsec    = sec_col.count_documents({})
        stats2      = sec_db.command('dbStats')
        used_dbSize2 = (stats2['dataSize']/(1024*1024)) + (stats2['indexSize']/(1024*1024))
        free_dbSize2 = 512 - used_dbSize2
        stats3      = mydb.command('dbStats')
        used_dbSize3 = (stats3['dataSize']/(1024*1024)) + (stats3['indexSize']/(1024*1024))
        free_dbSize3 = 512 - used_dbSize3

        multi_stats = base_stats + (
            f"\n\n<b>📦 Multi-DB Breakdown:</b>\n"
            f"DB1 Files: <code>{filesp}</code> | DB2 Files: <code>{totalsec}</code>\n"
            f"DB2: Used <code>{round(used_dbSize2,2)} MB</code> | Free <code>{round(free_dbSize2,2)} MB</code>\n"
            f"DB3: Used <code>{round(used_dbSize3,2)} MB</code> | Free <code>{round(free_dbSize3,2)} MB</code>"
        )
        await rju.edit(multi_stats, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        await rju.edit(f"<b>Error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command('invite') & filters.user(ADMINS))
async def gen_invite(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    try:
        link = await bot.create_chat_invite_link(chat)
    except ChatAdminRequired:
        return await message.reply("Invite Link Generation Failed, Iam Not Having Sufficient Rights")
    except Exception as e:
        return await message.reply(f'Error {e}')
    await message.reply(f'Here is your Invite Link {link.invite_link}')

@Client.on_message(filters.command('ban') & filters.user(ADMINS))
async def ban_a_user(bot, message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text(
            "<b>❌ User ID / Username daalo!\n\n"
            "✅ Format: <code>/ban user_id reason</code>\n"
            "🔸 Example: <code>/ban 123456789 Spamming</code>\n\n"
            "💡 Reply mode bhi kaam karta hai!</b>",
            parse_mode=enums.ParseMode.HTML
        )
    if message.reply_to_message and message.reply_to_message.from_user:
        k = message.reply_to_message.from_user
        reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason provided"
    else:
        r = message.text.split(None)
        if len(r) > 2:
            reason = message.text.split(None, 2)[2]
            chat_id = message.text.split(None, 2)[1]
        else:
            chat_id = message.command[1]
            reason = "No reason provided"
        try:
            chat_id = int(chat_id)
        except Exception:
            pass
        try:
            k = await bot.get_users(chat_id)
        except PeerIdInvalid:
            return await message.reply_text("<b>❌ Invalid user!</b>", parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            return await message.reply_text(f"<b>❌ Error: {e}</b>", parse_mode=enums.ParseMode.HTML)
    jar = await db.get_ban_status(k.id)
    if jar['is_banned']:
        return await message.reply_text(
            f"<b>⚠️ {k.mention} pehle se banned hai!\n\n"
            f"📋 Reason: {jar['ban_reason']}\n\n"
            f"Unban: <code>/unban {k.id}</code></b>",
            parse_mode=enums.ParseMode.HTML
        )
    await db.ban_user(k.id, reason)
    temp.BANNED_USERS.append(k.id)
    await message.reply_text(
        f"<blockquote><b>🔨 User Banned!\n\n"
        f"👤 User: {k.mention}\n"
        f"🆔 ID: <code>{k.id}</code>\n"
        f"📋 Reason: {reason}\n\n"
        f"Unban: <code>/unban {k.id}</code></b></blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
    try:
        await bot.send_message(
            k.id,
            f"<b>🚫 Aapko is bot se ban kar diya gaya hai.\n\n📋 Reason: {reason}</b>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass

@Client.on_message(filters.command('unban') & filters.user(ADMINS))
async def unban_a_user(bot, message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text(
            "<b>❌ User ID daalo!\n\n"
            "✅ Format: <code>/unban user_id</code></b>",
            parse_mode=enums.ParseMode.HTML
        )
    if message.reply_to_message and message.reply_to_message.from_user:
        k = message.reply_to_message.from_user
    else:
        chat_id = message.command[1]
        try:
            chat_id = int(chat_id)
        except Exception:
            pass
        try:
            k = await bot.get_users(chat_id)
        except Exception as e:
            return await message.reply_text(f"<b>❌ Error: {e}</b>", parse_mode=enums.ParseMode.HTML)
    jar = await db.get_ban_status(k.id)
    if not jar['is_banned']:
        return await message.reply_text(
            f"<b>⚠️ {k.mention} banned nahi hai!</b>",
            parse_mode=enums.ParseMode.HTML
        )
    await db.remove_ban(k.id)
    if k.id in temp.BANNED_USERS:
        temp.BANNED_USERS.remove(k.id)
    await message.reply_text(
        f"<blockquote><b>✅ User Unbanned!\n\n"
        f"👤 User: {k.mention}\n"
        f"🆔 ID: <code>{k.id}</code></b></blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
    try:
        await bot.send_message(k.id, "<b>✅ Aapka ban hata diya gaya!</b>", parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass
    
@Client.on_message(filters.command('users') & filters.user(ADMINS))
async def list_users(bot, message):
    # https://t.me/GetTGLink/4184
    raju = await message.reply('Getting List Of Users')
    users = await db.get_all_users()
    out = "Users Saved In DB Are:\n\n"
    async for user in users:
        out += f"<a href=tg://user?id={user['id']}>{user['name']}</a>"
        if user['ban_status']['is_banned']:
            out += '( Banned User )'
        out += '\n'
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open('users.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('users.txt', caption="List Of Users")

@Client.on_message(filters.command('chats') & filters.user(ADMINS))
async def list_chats(bot, message):
    status = await message.reply_text(
        "<b>⏳ Groups check ho raha hai, thoda wait karo...</b>",
        parse_mode=enums.ParseMode.HTML
    )

    active_list  = []
    inactive_ids = []

    try:
        all_chats = await db.grp.find({}).to_list(length=None)
    except Exception:
        try:
            all_chats = []
            async for c in db.grp.find({}):
                all_chats.append(c)
        except Exception:
            all_chats = []

    for chat in all_chats:
        chat_id = chat.get("id")
        if not chat_id:
            continue
        title = chat.get("title", "Unknown")
        try:
            await bot.get_chat(int(chat_id))
            active_list.append((chat_id, title))
        except Exception:
            inactive_ids.append(chat_id)

    for cid in inactive_ids:
        try:
            await db.grp.delete_one({"id": cid})
        except Exception:
            pass

    total   = len(all_chats)
    active  = len(active_list)
    removed = len(inactive_ids)

    out = (
        f"<b>📊 Groups Report</b>\n\n"
        f"✅ Active: <b>{active}</b>\n"
        f"🗑 Removed (inactive): <b>{removed}</b>\n"
        f"📋 Total: <b>{total}</b>\n\n"
    )

    if active_list:
        out += "<b>🔹 Active Groups:</b>\n"
        for gid, gtitle in active_list[:40]:
            out += f"• <b>{gtitle}</b> — <code>{gid}</code>\n"
        if active > 40:
            out += f"<i>...aur {active - 40} groups</i>\n"
    else:
        out += "<i>Koi active group nahi mila.</i>"

    try:
        await status.edit(out, parse_mode=enums.ParseMode.HTML)
    except Exception:
        clean = out.replace("<b>","").replace("</b>","").replace("<code>","").replace("</code>","").replace("<i>","").replace("</i>","")
        with open("/tmp/chats.txt", "w") as f:
            f.write(clean)
        await message.reply_document("/tmp/chats.txt", caption="Groups List")
        await status.delete()

