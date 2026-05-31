# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
from os import environ
from Script import script

id_pattern = re.compile(r'^.\d+$')

# Helper: String ko sahi se bool mein convert karo
# environ.get() string deta hai — bool("False") = True hota hai Python mein, isliye ye fix zaroori hai
def _bool(val, default=False):
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return val.strip().lower() not in ("false", "0", "no", "off", "none", "")


# ══════════════════════════════════════════════════════════════
#   BOT INFORMATION
# ══════════════════════════════════════════════════════════════
SESSION   = environ.get('SESSION', 'asbhaibsr')
API_ID    = int(environ.get('API_ID', '29970536'))
API_HASH  = environ.get('API_HASH', 'f4bfdcdd4a5c1b7328a7e4f25f024a09')
BOT_TOKEN = environ.get('BOT_TOKEN', "")


# ══════════════════════════════════════════════════════════════
#   PICTURES  (Start message ke liye, ek se zyada de sakte ho space se)
# ══════════════════════════════════════════════════════════════
PICS = (environ.get('PICS', 'https://i.postimg.cc/ZKmRdLtK/Arsad.jpg')).split()


# ══════════════════════════════════════════════════════════════
#   ADMINS & AUTH USERS
# ══════════════════════════════════════════════════════════════
ADMINS = [int(admin) if id_pattern.search(admin) else admin
          for admin in environ.get('ADMINS', '7315805581').split()]

auth_users = [int(user) if id_pattern.search(user) else user
              for user in environ.get('AUTH_USERS', '7315805581').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []


# ══════════════════════════════════════════════════════════════
#   CHANNELS
# ══════════════════════════════════════════════════════════════

# Jab user bot start kare ya group mein add ho to log yahan aata hai
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002352329534'))

# Jis channel mein file upload karo — bot automatically database mein save karta hai
CHANNELS = [int(ch) if id_pattern.search(ch) else ch
            for ch in environ.get('CHANNELS', '-1002463804038').split()]

# Force Subscribe Channel (AUTH_CHANNEL)
# REQUEST_TO_JOIN_MODE = True  →  request to join wali FSub
# REQUEST_TO_JOIN_MODE = False →  normal FSub
REQUEST_TO_JOIN_MODE = _bool(environ.get('REQUEST_TO_JOIN_MODE'), default=True)
TRY_AGAIN_BTN        = _bool(environ.get('TRY_AGAIN_BTN'),        default=True)

auth_channel = environ.get('AUTH_CHANNEL', '-1002892671107')
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None

# Movie request channel — user /request ya #request se movie maange
reqst_channel = environ.get('REQST_CHANNEL', '-1002588015375')
REQST_CHANNEL = int(reqst_channel) if reqst_channel and id_pattern.search(reqst_channel) else None

# Index request channel
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', LOG_CHANNEL))

# Support group ID — is group mein bot file nahi dega, sirf support karega
support_chat_id = environ.get('SUPPORT_CHAT_ID', '-1002588015375')
SUPPORT_CHAT_ID = int(support_chat_id) if support_chat_id and id_pattern.search(support_chat_id) else None

# /batch command ke liye file store channel
FILE_STORE_CHANNEL = [int(ch) for ch in (environ.get('FILE_STORE_CHANNEL', '-1002352329534')).split()]

# Delete index channel — yahan file forward karo to DB se delete ho jaegi
DELETE_CHANNELS = [int(dch) if id_pattern.search(dch) else dch
                   for dch in environ.get('DELETE_CHANNELS', '-1002352329534').split()]


# ══════════════════════════════════════════════════════════════
#   MONGODB DATABASE
# ══════════════════════════════════════════════════════════════
DATABASE_URI  = environ.get('DATABASE_URI',  "mongodb+srv://arsadbhaibsr1:yp8jnsfPx43jJthu@cluster0.kzp8k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = environ.get('DATABASE_NAME', "arsadbhaibsr1")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'arsadbhaibsr1')

# MULTIPLE_DATABASE = True  →  files 2 alag databases mein save hongi (zyada storage)
# MULTIPLE_DATABASE = False →  sirf ek database
MULTIPLE_DATABASE = _bool(environ.get('MULTIPLE_DATABASE'), default=True)

# Agar MULTIPLE_DATABASE True hai to neeche wale 3 DB URI fill karo
O_DB_URI = environ.get('O_DB_URI', "mongodb+srv://varex23967:Fs1gSm3vzlfVTpIb@cluster0.kvd5504.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")   # Other data DB
F_DB_URI = environ.get('F_DB_URI', "mongodb+srv://forokah246:D8WpfIARQE5hRPZT@cluster0.pv6aojo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")   # File DB (primary)
S_DB_URI = environ.get('S_DB_URI', "mongodb+srv://teroy33892:fNpMtrKkioyHMGEc@cluster0.ssbscwz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")   # File DB (secondary, jab primary full ho)


# ══════════════════════════════════════════════════════════════
#   PREMIUM & REFERRAL SYSTEM
# ══════════════════════════════════════════════════════════════
# PREMIUM_AND_REFERAL_MODE = True  → Premium aur Referral system ON
# PREMIUM_AND_REFERAL_MODE = False → Sab ke liye free, koi premium nahi
PREMIUM_AND_REFERAL_MODE = _bool(environ.get('PREMIUM_AND_REFERAL_MODE'), default=True)

# Referral system: kitne referrals pe premium milega aur kitne time ke liye
REFERAL_COUNT         = int(environ.get('REFERAL_COUNT', '10'))
REFERAL_PREMEIUM_TIME = environ.get('REFERAL_PREMEIUM_TIME', '2day')  # e.g. 1day, 1week, 1month

# Payment QR image URL (apna QR code ka link dalo)
PAYMENT_QR = environ.get('PAYMENT_QR', 'https://envs.sh/GdE.jpg')

# Ye PAYMENT_TEXT ab sirf /myplan mein use hota hai, /plan ke liye premium_plan.py use karo
PAYMENT_TEXT = environ.get('PAYMENT_TEXT', (
    '<b>- ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴀɴs -\n\n'
    '🥉 Bronze - ₹30 - 1 Week\n'
    '🥇 Gold   - ₹80 - 1 Month\n'
    '💎 Diamond - ₹250 - 6 Months\n\n'
    '🎁 ᴘʀᴇᴍɪᴜᴍ ғᴇᴀᴛᴜʀᴇs:\n'
    '○ No Verify\n○ Direct Files\n○ No Ads\n○ Fast Access\n\n'
    '✨ UPI: <code>arsadsaifi8272@ibl</code>\n\n'
    '/plan command se plan lo</b>'
))


# ══════════════════════════════════════════════════════════════
#   CLONE BOT
# ══════════════════════════════════════════════════════════════
CLONE_MODE         = _bool(environ.get('CLONE_MODE'), default=False)
CLONE_DATABASE_URI = environ.get('CLONE_DATABASE_URI', "")
PUBLIC_FILE_CHANNEL = environ.get('PUBLIC_FILE_CHANNEL', '')


# ══════════════════════════════════════════════════════════════
#   LINKS
# ══════════════════════════════════════════════════════════════
GRP_LNK      = environ.get('GRP_LNK',      'https://t.me/all_movies_webseries_is_here')
CHNL_LNK     = environ.get('CHNL_LNK',     'https://t.me/asbhai_bsr')
SUPPORT_CHAT = environ.get('SUPPORT_CHAT',  'aschat_group')   # @ ya https:// mat lagao
OWNER_LNK    = environ.get('OWNER_LNK',     'https://t.me/asbhaibsr')


# ══════════════════════════════════════════════════════════════
#   TRUE / FALSE SETTINGS
# ══════════════════════════════════════════════════════════════
AI_SPELL_CHECK       = _bool(environ.get('AI_SPELL_CHECK'),       default=True)
PM_SEARCH            = _bool(environ.get('PM_SEARCH'),            default=True)
BUTTON_MODE          = _bool(environ.get('BUTTON_MODE'),          default=False)
MAX_BTN              = _bool(environ.get('MAX_BTN'),              default=True)
IS_TUTORIAL          = _bool(environ.get('IS_TUTORIAL'),          default=False)
IMDB                 = _bool(environ.get('IMDB'),                 default=False)
AUTO_FFILTER         = _bool(environ.get('AUTO_FFILTER'),         default=True)
AUTO_DELETE          = _bool(environ.get('AUTO_DELETE'),          default=True)
LONG_IMDB_DESCRIPTION = _bool(environ.get('LONG_IMDB_DESCRIPTION'), default=False)
SPELL_CHECK_REPLY    = _bool(environ.get('SPELL_CHECK_REPLY'),    default=True)
MELCOW_NEW_USERS     = _bool(environ.get('MELCOW_NEW_USERS'),     default=True)
PROTECT_CONTENT      = _bool(environ.get('PROTECT_CONTENT'),      default=False)
PUBLIC_FILE_STORE    = _bool(environ.get('PUBLIC_FILE_STORE'),    default=True)
NO_RESULTS_MSG       = _bool(environ.get('NO_RESULTS_MSG'),       default=False)
USE_CAPTION_FILTER   = _bool(environ.get('USE_CAPTION_FILTER'),   default=True)


# ══════════════════════════════════════════════════════════════
#   TOKEN VERIFICATION
# ══════════════════════════════════════════════════════════════
# VERIFY = True  → User ko shortlink verify karna padega file lene se pehle (24h valid)
# VERIFY = False → Direct file milegi bina verify ke
VERIFY               = _bool(environ.get('VERIFY'), default=True)
VERIFY_SHORTLINK_URL = environ.get('VERIFY_SHORTLINK_URL', 'shortxlinks.com')
VERIFY_SHORTLINK_API = environ.get('VERIFY_SHORTLINK_API', '3e053189c26ffbc17fec79a7e456beffdebb4314')
VERIFY_TUTORIAL      = environ.get('VERIFY_TUTORIAL', 'https://t.me/Asbhai_bsr/504')

# Second shortener — agar True karo to dono shorteners se link banta hai (double earn)
VERIFY_SECOND_SHORTNER  = _bool(environ.get('VERIFY_SECOND_SHORTNER'), default=False)
VERIFY_SND_SHORTLINK_URL = environ.get('VERIFY_SND_SHORTLINK_URL', '')
VERIFY_SND_SHORTLINK_API = environ.get('VERIFY_SND_SHORTLINK_API', '')

# ══════════════════════════════════════════════════════════════
#   BLOGGER VERIFY SYSTEM (Shortlink ki jagah Blogger post use hogi)
# ══════════════════════════════════════════════════════════════
# BLOGGER_VERIFY = True  → Shortlink ki jagah Blogger post se verify hoga
# BLOGGER_VERIFY = False → Normal shortlink se verify hoga (purana tarika)
BLOGGER_VERIFY       = _bool(environ.get('BLOGGER_VERIFY'), default=False)

# Tumhara Blogger blog ka base URL (last mein / zaroor lagao)
# Example: 'https://asbhaibsr.blogspot.com/'
BLOGGER_BASE_URL     = environ.get('BLOGGER_BASE_URL', 'https://oyehero172.blogspot.com')

# Google Sheet CSV export URL — random post links yahan se aayenge
# Sheet mein sirf ek column honi chahiye: Post URL (header ke bina)
# Sheet → File → Share → Publish to web → CSV → us URL ko paste karo
# Example: 'https://docs.google.com/spreadsheets/d/SHEET_ID/export?format=csv&gid=0'
GOOGLE_SHEET_CSV_URL = environ.get('GOOGLE_SHEET_CSV_URL', 'https://docs.google.com/spreadsheets/d/1j0QcRjoq20yP-BgOpLW562Kshtr-BLMwVTAgviBsjDY/export?format=csv&gid=0')


# ══════════════════════════════════════════════════════════════
#   SHORTLINK (Group-wise shortlink for file buttons)
# ══════════════════════════════════════════════════════════════
SHORTLINK_MODE = _bool(environ.get('SHORTLINK_MODE'), default=False)
SHORTLINK_URL  = environ.get('SHORTLINK_URL', '')
SHORTLINK_API  = environ.get('SHORTLINK_API', '')
TUTORIAL       = environ.get('TUTORIAL', '')  # Shortlink open karne ka tutorial video link


# ══════════════════════════════════════════════════════════════
#   OTHER SETTINGS
# ══════════════════════════════════════════════════════════════
CACHE_TIME          = int(environ.get('CACHE_TIME', 1800))
MAX_B_TN            = environ.get("MAX_B_TN", "5")
PORT                = environ.get("PORT", "8080")
MSG_ALRT            = environ.get('MSG_ALRT', 'Hello My Dear Friends ❤️')
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", f"{script.CAPTION}")
BATCH_FILE_CAPTION  = environ.get("BATCH_FILE_CAPTION", CUSTOM_FILE_CAPTION)
IMDB_TEMPLATE       = environ.get("IMDB_TEMPLATE", f"{script.IMDB_TEMPLATE_TXT}")
MAX_LIST_ELM        = environ.get("MAX_LIST_ELM", None)


# ══════════════════════════════════════════════════════════════
#   FILTER BUTTONS OPTIONS  (Language / Season / Episode / Quality / Year)
# ══════════════════════════════════════════════════════════════
LANGUAGES = ["malayalam", "mal", "tamil", "tam", "english", "eng",
             "hindi", "hin", "telugu", "tel", "kannada", "kan"]

SEASONS = ["season 1", "season 2", "season 3", "season 4", "season 5",
           "season 6", "season 7", "season 8", "season 9", "season 10"]

EPISODES = [
    "E01","E02","E03","E04","E05","E06","E07","E08","E09","E10",
    "E11","E12","E13","E14","E15","E16","E17","E18","E19","E20",
    "E21","E22","E23","E24","E25","E26","E27","E28","E29","E30",
    "E31","E32","E33","E34","E35","E36","E37","E38","E39","E40",
]

QUALITIES = ["360p", "480p", "720p", "1080p", "1440p", "2160p"]

YEARS = [
    "1900","1991","1992","1993","1994","1995","1996","1997","1998","1999",
    "2000","2001","2002","2003","2004","2005","2006","2007","2008","2009",
    "2010","2011","2012","2013","2014","2015","2016","2017","2018","2019",
    "2020","2021","2022","2023","2024","2025","2026",
]


# ══════════════════════════════════════════════════════════════
#   ONLINE STREAM & DOWNLOAD
# ══════════════════════════════════════════════════════════════
STREAM_MODE      = _bool(environ.get('STREAM_MODE'), default=True)
MULTI_CLIENT     = False
SLEEP_THRESHOLD  = int(environ.get('SLEEP_THRESHOLD', '60'))
PING_INTERVAL    = int(environ.get("PING_INTERVAL", "1200"))   # 20 minutes

if 'DYNO' in environ:
    ON_HEROKU = True
else:
    ON_HEROKU = False

URL = environ.get("URL", "https://depressed-cornelle-asbhaibsr-179ba27d.koyeb.app/")


# ══════════════════════════════════════════════════════════════
#   RENAME MODE
# ══════════════════════════════════════════════════════════════
RENAME_MODE = _bool(environ.get('RENAME_MODE'), default=True)


# ══════════════════════════════════════════════════════════════
#   AUTO APPROVE  (Join request auto approve)
# ══════════════════════════════════════════════════════════════
AUTO_APPROVE_MODE = _bool(environ.get('AUTO_APPROVE_MODE'), default=False)


# ══════════════════════════════════════════════════════════════
#   START REACTIONS
# ══════════════════════════════════════════════════════════════
REACTIONS = [
    "🤝","😇","🤗","😍","👍","🎅","😐","🥰","🤩","😱",
    "🤣","😘","👏","😛","😈","🎉","⚡️","🫡","🤓","😎",
    "🏆","🔥","🤭","🌚","🆒","👻","😁",
]


# ══════════════════════════════════════════════════════════════
#   DATABASE URI ASSIGNMENT  (MULTIPLE_DATABASE ke basis pe)
# ══════════════════════════════════════════════════════════════
if MULTIPLE_DATABASE:
    # Sab ek hi main database use karte hain (Heroku/Koyeb free tier ke liye)
    USER_DB_URI    = DATABASE_URI
    OTHER_DB_URI   = DATABASE_URI
    FILE_DB_URI    = DATABASE_URI
    SEC_FILE_DB_URI = DATABASE_URI
else:
    USER_DB_URI    = DATABASE_URI   # User data
    OTHER_DB_URI   = O_DB_URI       # Other data
    FILE_DB_URI    = F_DB_URI       # Files (primary)
    SEC_FILE_DB_URI = S_DB_URI      # Files (secondary)


# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

# ══════════════════════════════════════════════════════════════
#   ANTI-SPAM & SEARCH LIMIT
# ══════════════════════════════════════════════════════════════
# Free user ke liye daily PM search limit (0 = unlimited)
PM_SEARCH_DAILY_LIMIT = int(environ.get('PM_SEARCH_DAILY_LIMIT', '15'))

# Spam threshold: N messages in T seconds → block for B seconds
SPAM_MSG_LIMIT   = int(environ.get('SPAM_MSG_LIMIT',   '5'))   # N messages
SPAM_TIME_WINDOW = int(environ.get('SPAM_TIME_WINDOW', '5'))   # T seconds
SPAM_BLOCK_TIME  = int(environ.get('SPAM_BLOCK_TIME', '60'))   # B seconds block

# ══════════════════════════════════════════════════════════════
#   MAINTENANCE MODE
# ══════════════════════════════════════════════════════════════
# Bot startup pe off rehta hai, /maintenance on/off se toggle hota hai
# env var set karna ho to: MAINTENANCE_MODE=True
MAINTENANCE_MODE = _bool(environ.get('MAINTENANCE_MODE'), default=False)
