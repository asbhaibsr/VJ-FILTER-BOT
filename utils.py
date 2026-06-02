# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import logging, asyncio, os, re, random, pytz, aiohttp, requests, string, json, http.client
from info import *
from imdb import Cinemagoer 
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from pyrogram.errors import *
from typing import Union
from Script import script
from datetime import datetime, date
from typing import List
from database.users_chats_db import db
from database.join_reqs import JoinReqs
from bs4 import BeautifulSoup
from shortzy import Shortzy

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
#   ANTI-SPAM RATE LIMITER
# ══════════════════════════════════════════════════════════════
import time as _time

_SPAM_TRACKER  = {}   # user_id -> [timestamp, timestamp, ...]
_SPAM_BLOCKED  = {}   # user_id -> blocked_until (float timestamp)
_PM_SEARCH_CTR = {}   # user_id -> {"date": "YYYY-MM-DD", "count": int}

async def is_spam(user_id: int) -> bool:
    """Returns True if user is spamming (should be ignored)"""
    try:
        from info import SPAM_MSG_LIMIT, SPAM_TIME_WINDOW, SPAM_BLOCK_TIME
    except ImportError:
        SPAM_MSG_LIMIT, SPAM_TIME_WINDOW, SPAM_BLOCK_TIME = 5, 5, 60

    now = _time.time()

    # Check if still blocked
    if user_id in _SPAM_BLOCKED:
        if now < _SPAM_BLOCKED[user_id]:
            return True
        else:
            del _SPAM_BLOCKED[user_id]

    # Track message timestamps
    timestamps = _SPAM_TRACKER.get(user_id, [])
    timestamps = [t for t in timestamps if now - t < SPAM_TIME_WINDOW]
    timestamps.append(now)
    _SPAM_TRACKER[user_id] = timestamps

    # Block if exceeded limit
    if len(timestamps) >= SPAM_MSG_LIMIT:
        _SPAM_BLOCKED[user_id] = now + SPAM_BLOCK_TIME
        _SPAM_TRACKER[user_id] = []
        return True
    return False


async def check_pm_search_limit(user_id: int) -> tuple:
    """
    Returns (allowed: bool, remaining: int)
    Premium users always allowed.
    Free users: limited by PM_SEARCH_DAILY_LIMIT per day (IST).
    """
    try:
        from info import PM_SEARCH_DAILY_LIMIT
        from database.users_chats_db import db
        import pytz
        from datetime import date
    except ImportError:
        return True, 999

    if PM_SEARCH_DAILY_LIMIT <= 0:
        return True, 999

    # Premium users unlimited
    try:
        if await db.has_premium_access(user_id):
            return True, 999
    except Exception:
        pass

    tz = pytz.timezone('Asia/Kolkata')
    today = date.today().strftime("%Y-%m-%d")
    data  = _PM_SEARCH_CTR.get(user_id, {"date": "", "count": 0})

    if data["date"] != today:
        data = {"date": today, "count": 0}

    if data["count"] >= PM_SEARCH_DAILY_LIMIT:
        return False, 0

    data["count"] += 1
    _PM_SEARCH_CTR[user_id] = data
    remaining = PM_SEARCH_DAILY_LIMIT - data["count"]
    return True, remaining


logger.setLevel(logging.INFO)
join_db = JoinReqs
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)\]\((buttonurl|buttonalert):(?:/{0,2})(.+?)(:same)?\))")

imdb = Cinemagoer() 
TOKENS = {}
VERIFIED = {}
# Structure: {user_id: {"v1": unix_timestamp, "v2": unix_timestamp_or_0}}
# v1 = first verify time, v2 = second verify time (12h gap required)
# Access allowed 24h total: v1 → 12h free → v2 required → 12h free → v1 again
import time as _time_module
BANNED = {}
SECOND_SHORTENER = {}
SMART_OPEN = '“'
SMART_CLOSE = '”'
START_CHAR = ('\'', '"', SMART_OPEN)

# temp db for banned 
class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    BOT = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None
    GETALL = {}
    SHORT = {}
    SETTINGS = {}
    IMDB_CAP = {}


async def pub_is_subscribed(bot, query, channel):
    btn = []
    for id in channel:
        chat = await bot.get_chat(int(id))
        try:
            await bot.get_chat_member(id, query.from_user.id)
        except UserNotParticipant:
            btn.append(
                [InlineKeyboardButton(f'Join {chat.title}', url=chat.invite_link)]
            )
        except Exception as e:
            pass
    return btn

async def is_subscribed(bot, query):
    if REQUEST_TO_JOIN_MODE == True and join_db().isActive():
        try:
            user = await join_db().get_user(query.from_user.id)
            if user and user["user_id"] == query.from_user.id:
                return True
            else:
                try:
                    user_data = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
                except UserNotParticipant:
                    pass
                except Exception as e:
                    logger.exception(e)
                else:
                    if user_data.status != enums.ChatMemberStatus.BANNED:
                        return True
        except Exception as e:
            logger.exception(e)
            return False
    else:
        try:
            user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
        except UserNotParticipant:
            pass
        except Exception as e:
            logger.exception(e)
        else:
            if user.status != enums.ChatMemberStatus.BANNED:
                return True
        return False

async def get_poster(query, bulk=False, id=False, file=None):
    if not id:
        query = (query.strip()).lower()
        title = query
        year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
        if year:
            year = list_to_str(year[:1])
            title = (query.replace(year, "")).strip()
        elif file is not None:
            year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
            if year:
                year = list_to_str(year[:1]) 
        else:
            year = None
        loop = asyncio.get_event_loop()
        movieid = await loop.run_in_executor(None, lambda: imdb.search_movie(title.lower(), results=10))
        if not movieid:
            return None
        if year:
            filtered=list(filter(lambda k: str(k.get('year')) == str(year), movieid))
            if not filtered:
                filtered = movieid
        else:
            filtered = movieid
        movieid=list(filter(lambda k: k.get('kind') in ['movie', 'tv series'], filtered))
        if not movieid:
            movieid = filtered
        if bulk:
            return movieid
        movieid = movieid[0].movieID
    else:
        movieid = query
    loop = asyncio.get_event_loop()
    movie = await loop.run_in_executor(None, lambda: imdb.get_movie(movieid))
    if not movie:
        return None
    if movie.get("original air date"):
        date = movie["original air date"]
    elif movie.get("year"):
        date = movie.get("year")
    else:
        date = "N/A"
    plot = ""
    if not LONG_IMDB_DESCRIPTION:
        plot = movie.get('plot')
        if plot and len(plot) > 0:
            plot = plot[0]
    else:
        plot = movie.get('plot outline')
    if plot and len(plot) > 800:
        plot = plot[0:800] + "..."

    return {
        'title': movie.get('title'),
        'votes': movie.get('votes'),
        "aka": list_to_str(movie.get("akas")),
        "seasons": movie.get("number of seasons"),
        "box_office": movie.get('box office'),
        'localized_title': movie.get('localized title'),
        'kind': movie.get("kind"),
        "imdb_id": f"tt{movie.get('imdbID')}",
        "cast": list_to_str(movie.get("cast")),
        "runtime": list_to_str(movie.get("runtimes")),
        "countries": list_to_str(movie.get("countries")),
        "certificates": list_to_str(movie.get("certificates")),
        "languages": list_to_str(movie.get("languages")),
        "director": list_to_str(movie.get("director")),
        "writer":list_to_str(movie.get("writer")),
        "producer":list_to_str(movie.get("producer")),
        "composer":list_to_str(movie.get("composer")) ,
        "cinematographer":list_to_str(movie.get("cinematographer")),
        "music_team": list_to_str(movie.get("music department")),
        "distributors": list_to_str(movie.get("distributors")),
        'release_date': date,
        'year': movie.get('year'),
        'genres': list_to_str(movie.get("genres")),
        'poster': movie.get('full-size cover url'),
        'plot': plot,
        'rating': str(movie.get("rating")),
        'url':f'https://www.imdb.com/title/tt{movieid}'
    }

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def broadcast_messages_group(chat_id, message):
    try:
        kd = await message.copy(chat_id=chat_id)
        try:
            await kd.pin()
        except:
            pass
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages_group(chat_id, message)
    except Exception as e:
        err = str(e).lower()
        # Auto-remove groups where bot is banned/kicked/not member
        if any(x in err for x in ['kicked', 'banned', 'not a member', 'chat_write_forbidden', 
                                    'channel_private', 'peer_id_invalid', 'chat not found']):
            await db.disable_chat(int(chat_id), "Bot was kicked or group unavailable")
            logging.info(f"Group {chat_id} auto-disabled: {e}")
        return False, "Error"
    
async def search_gagala(text):
    usr_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/61.0.3163.100 Safari/537.36'
        }
    text = text.replace(" ", '+')
    url = f'https://www.google.com/search?q={text}'
    response = requests.get(url, headers=usr_agent)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = soup.find_all( 'h3' )
    return [title.getText() for title in titles]

async def get_settings(group_id):
    settings = await db.get_settings(group_id)
    return settings
    
async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current.update({key: value})
    await db.update_settings(group_id, current)
    
def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]  

def get_file_id(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker"
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj

def extract_user(message: Message) -> Union[int, str]:
    user_id = None
    user_first_name = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name

    elif len(message.command) > 1:
        if (
            len(message.entities) > 1 and
            message.entities[1].type == enums.MessageEntityType.TEXT_MENTION
        ):
           
            required_entity = message.entities[1]
            user_id = required_entity.user.id
            user_first_name = required_entity.user.first_name
        else:
            user_id = message.command[1]
            # don't want to make a request -_-
            user_first_name = user_id
        try:
            user_id = int(user_id)
        except ValueError:
            pass
    else:
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name
    return (user_id, user_first_name)

def list_to_str(k):
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    elif MAX_LIST_ELM:
        k = k[:int(MAX_LIST_ELM)]
        return ' '.join(f'{elem}, ' for elem in k)
    else:
        return ' '.join(f'{elem}, ' for elem in k)

def last_online(from_user):
    time = ""
    if from_user.is_bot:
        time += "🤖 Bot :("
    elif from_user.status == enums.UserStatus.RECENTLY:
        time += "Recently"
    elif from_user.status == enums.UserStatus.LAST_WEEK:
        time += "Within the last week"
    elif from_user.status == enums.UserStatus.LAST_MONTH:
        time += "Within the last month"
    elif from_user.status == enums.UserStatus.LONG_AGO:
        time += "A long time ago :("
    elif from_user.status == enums.UserStatus.ONLINE:
        time += "Currently Online"
    elif from_user.status == enums.UserStatus.OFFLINE:
        time += from_user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S")
    return time

def split_quotes(text: str) -> List:
    if not any(text.startswith(char) for char in START_CHAR):
        return text.split(None, 1)
    counter = 1  # ignore first char -> is some kind of quote
    while counter < len(text):
        if text[counter] == "\\":
            counter += 1
        elif text[counter] == text[0] or (text[0] == SMART_OPEN and text[counter] == SMART_CLOSE):
            break
        counter += 1
    else:
        return text.split(None, 1)

    # 1 to avoid starting quote, and counter is exclusive so avoids ending
    key = remove_escapes(text[1:counter].strip())
    # index will be in range, or `else` would have been executed and returned
    rest = text[counter + 1:].strip()
    if not key:
        key = text[0] + text[0]
    return list(filter(None, [key, rest]))

def gfilterparser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    try:
        return note_data, buttons, alerts
    except:
        return note_data, buttons, None

def parser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    try:
        return note_data, buttons, alerts
    except:
        return note_data, buttons, None

def remove_escapes(text: str) -> str:
    res = ""
    is_escaped = False
    for counter in range(len(text)):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
    return res

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'



async def get_clone_shortlink(link, url, api):
    return await _direct_shorten(link, url, api)
                           
async def get_shortlink(chat_id, link):
    settings = await get_settings(chat_id) #fetching settings for group
    if 'shortlink' in settings.keys():
        URL = settings['shortlink']
        API = settings['shortlink_api']
    else:
        URL = SHORTLINK_URL
        API = SHORTLINK_API
    if URL.startswith("shorturllink") or URL.startswith("terabox.in") or URL.startswith("urlshorten.in"):
        URL = SHORTLINK_URL
        API = SHORTLINK_API
    if URL == "api.shareus.io":
        url = f'https://{URL}/easy_api'
        params = {
            "key": API,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return link
    else:
        return await _direct_shorten(link, URL, API)

async def get_tutorial(chat_id):
    settings = await get_settings(chat_id) #fetching settings for group
    return settings['tutorial']
        
async def _direct_shorten(link, url, api, timeout_sec=5):
    # Direct aiohttp shortlink — Shortzy se fast aur reliable
    # shortxlinks, aroolink, aur baaki standard providers support karta hai
    if not url or not api:
        return link
    try:
        if url == 'api.shareus.io':
            req_url = f'https://{url}/easy_api'
            params = {'key': api, 'link': link}
        else:
            req_url = f'https://{url}/api'
            params = {'api': api, 'url': link, 'format': 'json'}
        _timeout = aiohttp.ClientTimeout(total=timeout_sec, connect=3)
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(timeout=_timeout, connector=conn) as session:
            async with session.get(req_url, params=params) as resp:
                if url == 'api.shareus.io':
                    return await resp.text()
                data = await resp.json(content_type=None)
                short = (
                    data.get('shortenedUrl')
                    or data.get('shortLink')
                    or data.get('short_link')
                    or data.get('shortened_url')
                    or data.get('short')
                )
                if short and short.startswith('http'):
                    return short
                logger.error(f'Shortlink API bad response ({url}): {data}')
                return link
    except Exception as e:
        logger.error(f'Shortlink conversion failed ({url}): {e}')
        return link


async def get_verify_shorted_link(link, url, api, timeout_sec=5):
    # Verify shortlink — original link return karo agar timeout ho
    return await _direct_shorten(link, url, api, timeout_sec=timeout_sec)
async def check_token(bot, userid, token):
    user = await bot.get_users(userid)
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
    if user.id in TOKENS.keys():
        TKN = TOKENS[user.id]
        if token in TKN.keys():
            is_used = TKN[token]
            if is_used == True:
                return False
            else:
                return True
    else:
        return False

async def get_random_blogger_post() -> str:
    """
    Google Sheet CSV se ek random Blogger post URL fetch karta hai.
    Saare columns mein se URLs collect karta hai — jis column mein bhi ho.
    GOOGLE_SHEET_CSV_URL aur BLOGGER_BASE_URL env vars mein set karo.
    """
    try:
        from info import GOOGLE_SHEET_CSV_URL, BLOGGER_BASE_URL
        if not GOOGLE_SHEET_CSV_URL:
            logger.warning("GOOGLE_SHEET_CSV_URL set nahi hai, BLOGGER_BASE_URL use ho raha hai.")
            return BLOGGER_BASE_URL or ""
        async with aiohttp.ClientSession() as session:
            async with session.get(GOOGLE_SHEET_CSV_URL, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                text = await resp.text()
        urls = []
        base = (BLOGGER_BASE_URL or "").rstrip("/")
        for line in text.splitlines():
            if not line.strip():
                continue
            # Saare columns check karo
            cols = [c.strip().strip('"') for c in line.split(',')]
            for raw in cols:
                if not raw:
                    continue
                if raw.startswith("http"):
                    urls.append(raw)
                elif raw.startswith("blogspot.com") or raw.startswith("www."):
                    urls.append("https://" + raw)
                elif "/" in raw and not raw.startswith("#") and base:
                    urls.append(f"{base}/{raw.lstrip('/')}")
        if not urls:
            logger.warning("Google Sheet mein koi valid URL nahi mili.")
            return base or ""
        return random.choice(urls)
    except Exception as e:
        logger.error(f"Blogger post fetch error: {e}")
        try:
            from info import BLOGGER_BASE_URL
            return BLOGGER_BASE_URL or ""
        except Exception:
            return ""


async def get_token(bot, userid, link):
    user = await bot.get_users(userid)
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    TOKENS[user.id] = {token: False}

    # ── BLOGGER VERIFY MODE ─────────────────────────────────────────────
    # Agar BLOGGER_VERIFY = True hai to shortlink ki jagah Blogger post
    # ka URL diya jaayega. User wahan ja ke verify karega, tab movie milegi.
    try:
        from info import BLOGGER_VERIFY, BLOGGER_BASE_URL
    except ImportError:
        BLOGGER_VERIFY = False
        BLOGGER_BASE_URL = ""

    if BLOGGER_VERIFY:
        # Bot ka start link jo verify ke baad open hoga
        bot_verify_link = f"{link}verify-{user.id}-{token}"
        # Random Blogger post fetch karo (Google Sheet se)
        blogger_post_url = await get_random_blogger_post()
        if not blogger_post_url:
            # Fallback: BLOGGER_BASE_URL use karo
            blogger_post_url = BLOGGER_BASE_URL or link
        # Blogger post URL mein verify params add karo
        # Format: https://yourblog.blogspot.com/post-name/?uid=USER_ID&token=TOKEN&bot=BOT_USERNAME
        sep = "&" if "?" in blogger_post_url else "?"
        import urllib.parse
        # Bot username (temp se lena) — late import to avoid circular
        try:
            from utils import temp as _temp
            bot_username = _temp.U_NAME
        except Exception:
            try:
                from TechVJ.bot import StreamBot
                bot_username = (await StreamBot.get_me()).username
            except Exception:
                bot_username = ""
        params = urllib.parse.urlencode({
            "uid": user.id,
            "token": token,
            "bot": bot_username,
        })
        final_url = f"{blogger_post_url}{sep}{params}"
        return str(final_url)
    # -- NORMAL SHORTLINK MODE --
    raw_link = f"{link}verify-{user.id}-{token}"

    # Step 1: Primary shortlink try karo
    shortened_verify_url = await get_verify_shorted_link(raw_link, VERIFY_SHORTLINK_URL, VERIFY_SHORTLINK_API)
    primary_failed = (shortened_verify_url == raw_link)

    if VERIFY_SECOND_SHORTNER:
        if primary_failed:
            # Primary down - secondary pe directly try karo
            logger.warning(f"Primary shortlink ({VERIFY_SHORTLINK_URL}) failed, trying secondary ({VERIFY_SND_SHORTLINK_URL})")
            snd_link = await get_verify_shorted_link(raw_link, VERIFY_SND_SHORTLINK_URL, VERIFY_SND_SHORTLINK_API)
        else:
            # Dono shortlinks double-wrap karo
            snd_link = await get_verify_shorted_link(shortened_verify_url, VERIFY_SND_SHORTLINK_URL, VERIFY_SND_SHORTLINK_API)
        return str(snd_link)
    else:
        return str(shortened_verify_url)

async def verify_user(bot, userid, token):
    user = await bot.get_users(userid)
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
    TOKENS[user.id] = {token: True}
    now_ts = _time_module.time()
    existing = VERIFIED.get(user.id, {})

    if not isinstance(existing, dict):
        # Old format — reset
        existing = {}

    v1 = existing.get("v1", 0)
    v2 = existing.get("v2", 0)

    if VERIFY_SECOND_SHORTNER:
        # 12-12 hour loop system
        # v1 done, v2 pending → save v2
        if v1 > 0 and (now_ts - v1) >= 43200 and v2 == 0:
            existing["v2"] = now_ts
        # Both expired OR fresh user → save v1, reset v2
        elif v1 == 0 or (v2 > 0 and (now_ts - v2) >= 43200):
            existing["v1"] = now_ts
            existing["v2"] = 0
        # v1 just done, too early for v2
        elif v1 > 0 and (now_ts - v1) < 43200:
            existing["v1"] = now_ts
    else:
        # Single verify — 24h valid
        existing["v1"] = now_ts
        existing["v2"] = 0

    VERIFIED[user.id] = existing
    # Log verify complete to LOG_CHANNEL
    try:
        import pytz as _pytz
        from datetime import datetime as dt
        _tz = _pytz.timezone('Asia/Kolkata')
        now = dt.now(_tz)
        time_str = now.strftime("%d %b %H:%M IST")
        shortlink_url = VERIFY_SHORTLINK_URL if VERIFY_SHORTLINK_URL else "N/A"
        log_text = (
            f"✅ #VerifyComplete\n\n"
            f"ɪᴅ - {user.id}\n"
            f"Nᴀᴍᴇ - {user.mention}\n"
            f"sʜᴏʀᴛʟɪɴᴋ - {shortlink_url}\n"
            f"ᴛɪᴍᴇ - {time_str}"
        )
        await bot.send_message(LOG_CHANNEL, log_text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Verify log error: {e}")

async def check_verification(bot, userid):
    user = await bot.get_users(userid)
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))

    now_ts = _time_module.time()
    data   = VERIFIED.get(user.id)

    if not data:
        return False

    # Old format (date string) — force re-verify
    if not isinstance(data, dict):
        return False

    v1 = data.get("v1", 0)
    v2 = data.get("v2", 0)

    if not VERIFY_SECOND_SHORTNER:
        # Single verify: valid 24h from v1
        return v1 > 0 and (now_ts - v1) < 86400

    # Dual verify: 12-12h loop
    # Phase 1: v1 done, v2 not yet — valid 12h
    if v1 > 0 and v2 == 0:
        return (now_ts - v1) < 43200
    # Phase 2: both done — valid 12h from v2
    if v1 > 0 and v2 > 0:
        return (now_ts - v2) < 43200
    return False


async def get_verify_time_remaining(userid) -> int:
    """Returns seconds remaining in current verify window (0 if expired)"""
    now_ts = _time_module.time()
    data   = VERIFIED.get(userid)
    if not data or not isinstance(data, dict):
        return 0
    v1 = data.get("v1", 0)
    v2 = data.get("v2", 0)
    if not VERIFY_SECOND_SHORTNER:
        rem = 86400 - (now_ts - v1) if v1 > 0 else 0
    elif v1 > 0 and v2 == 0:
        rem = 43200 - (now_ts - v1)
    elif v1 > 0 and v2 > 0:
        rem = 43200 - (now_ts - v2)
    else:
        rem = 0
    return max(0, int(rem))


async def needs_second_verify(userid) -> bool:
    """Check karo ki user ko abhi 2nd shortlink verify karni hai"""
    if not VERIFY_SECOND_SHORTNER:
        return False
    now_ts = _time_module.time()
    data   = VERIFIED.get(userid)
    if not data or not isinstance(data, dict):
        return False
    v1 = data.get("v1", 0)
    v2 = data.get("v2", 0)
    # v1 done, 12h passed, v2 pending
    return v1 > 0 and v2 == 0 and (now_ts - v1) >= 43200
    
async def send_all(bot, userid, files, ident, chat_id, user_name, query):
    settings = await get_settings(chat_id)
    if 'is_shortlink' in settings.keys():
        ENABLE_SHORTLINK = settings['is_shortlink']
    else:
        await save_group_settings(message.chat.id, 'is_shortlink', False)
        ENABLE_SHORTLINK = False
    try:
        if ENABLE_SHORTLINK:
            for file in files:
                title = file["file_name"]
                size = get_size(file["file_size"])
                if not await db.has_premium_access(userid) and SHORTLINK_MODE == True:
                    await bot.send_message(chat_id=userid, text=f"<b>Hᴇʏ ᴛʜᴇʀᴇ {user_name} 👋🏽 \n\n✅ Sᴇᴄᴜʀᴇ ʟɪɴᴋ ᴛᴏ ʏᴏᴜʀ ғɪʟᴇ ʜᴀs sᴜᴄᴄᴇssғᴜʟʟʏ ʙᴇᴇɴ ɢᴇɴᴇʀᴀᴛᴇᴅ ᴘʟᴇᴀsᴇ ᴄʟɪᴄᴋ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ\n\n🗃️ Fɪʟᴇ Nᴀᴍᴇ : {title}\n🔖 Fɪʟᴇ Sɪᴢᴇ : {size}</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Dᴏᴡɴʟᴏᴀᴅ 📥", url=await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=files_{file['file_id']}"))]]))
        else:
            for file in files:
                f_caption = file["caption"]
                title = file["file_name"]
                size = get_size(file["file_size"])
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption = CUSTOM_FILE_CAPTION.format(
                            file_name='' if title is None else title,
                            file_size='' if size is None else size,
                            file_caption='' if f_caption is None else f_caption
                        )
                    except Exception as e:
                        print(e)
                        f_caption = f_caption
                if f_caption is None:
                    f_caption = f"{title}"
                await bot.send_cached_media(
                    chat_id=userid,
                    file_id=file["file_id"],
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False,
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=GRP_LNK),
                            InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                        ],[
                            InlineKeyboardButton("Bᴏᴛ Oᴡɴᴇʀ", url=OWNER_LNK)
                        ]]
                    )
                )
    except UserIsBlocked:
        await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
    except PeerIdInvalid:
        await query.answer('Hᴇʏ, Sᴛᴀʀᴛ Bᴏᴛ Fɪʀsᴛ Aɴᴅ Cʟɪᴄᴋ Sᴇɴᴅ Aʟʟ', show_alert=True)
    except Exception as e:
        await query.answer('Hᴇʏ, Sᴛᴀʀᴛ Bᴏᴛ Fɪʀsᴛ Aɴᴅ Cʟɪᴄᴋ Sᴇɴᴅ Aʟʟ', show_alert=True)
        
async def get_cap(settings, remaining_seconds, files, query, total_results, search):
    if settings["imdb"]:
        IMDB_CAP = temp.IMDB_CAP.get(query.from_user.id)
        if IMDB_CAP:
            cap = IMDB_CAP
            cap+="<b>\n\n<u>🍿 Your Movie Files 👇</u></b>\n\n"
            for file in files:
                cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file['file_id']}'>[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}\n\n</a></b>"
        else:
            imdb = await get_poster(search, file=(files[0])["file_name"]) if settings["imdb"] else None
            if imdb:
                TEMPLATE = script.IMDB_TEMPLATE_TXT
                cap = TEMPLATE.format(
                    qurey=search,
                    title=imdb['title'],
                    votes=imdb['votes'],
                    aka=imdb["aka"],
                    seasons=imdb["seasons"],
                    box_office=imdb['box_office'],
                    localized_title=imdb['localized_title'],
                    kind=imdb['kind'],
                    imdb_id=imdb["imdb_id"],
                    cast=imdb["cast"],
                    runtime=imdb["runtime"],
                    countries=imdb["countries"],
                    certificates=imdb["certificates"],
                    languages=imdb["languages"],
                    director=imdb["director"],
                    writer=imdb["writer"],
                    producer=imdb["producer"],
                    composer=imdb["composer"],
                    cinematographer=imdb["cinematographer"],
                    music_team=imdb["music_team"],
                    distributors=imdb["distributors"],
                    release_date=imdb['release_date'],
                    year=imdb['year'],
                    genres=imdb['genres'],
                    poster=imdb['poster'],
                    plot=imdb['plot'],
                    rating=imdb['rating'],
                    url=imdb['url'],
                    **locals()
                )
                cap+="<b>\n\n<u>🍿 Your Movie Files 👇</u></b>\n\n"
                for file in files:
                    cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file['file_id']}'>[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}\n\n</a></b>"
            else:
                cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search}\n\nRᴇǫᴜᴇsᴛᴇᴅ Bʏ ☞ {query.from_user.mention}\n\nʀᴇsᴜʟᴛ sʜᴏᴡ ɪɴ ☞ {remaining_seconds} sᴇᴄᴏɴᴅs\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ ☞ : {query.message.chat.title}\n\n⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️\n\n</b>"
                cap+="<b><u>🍿 Your Movie Files 👇</u></b>\n\n"
                for file in files:
                    cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file['file_id']}'>[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}\n\n</a></b>"
    else:
        cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search}\n\nRᴇǫᴜᴇsᴛᴇᴅ Bʏ ☞ {query.from_user.mention}\n\nʀᴇsᴜʟᴛ sʜᴏᴡ ɪɴ ☞ {remaining_seconds} sᴇᴄᴏɴᴅs\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ ☞ : {query.message.chat.title} \n\n⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️\n\n</b>"
        cap+="<b><u>🍿 Your Movie Files 👇</u></b>\n\n"
        for file in files:
            cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file['file_id']}'>[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}\n\n</a></b>"
    return cap


async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:]
        if value:
            value = int(value)
        return value, unit
    value, unit = extract_value_and_unit(time_string)
    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0

