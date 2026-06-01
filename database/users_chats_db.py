# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
from pymongo.errors import DuplicateKeyError
import motor.motor_asyncio
from pymongo import MongoClient
from info import DATABASE_NAME, USER_DB_URI, OTHER_DB_URI, CUSTOM_FILE_CAPTION, IMDB, IMDB_TEMPLATE, MELCOW_NEW_USERS, BUTTON_MODE, SPELL_CHECK_REPLY, PROTECT_CONTENT, AUTO_DELETE, MAX_BTN, AUTO_FFILTER, SHORTLINK_API, SHORTLINK_URL, SHORTLINK_MODE, TUTORIAL, IS_TUTORIAL
import time
import datetime

my_client = MongoClient(OTHER_DB_URI)
mydb = my_client["referal_user"]

async def referal_add_user(user_id, ref_user_id):
    user_db = mydb[str(user_id)]
    user = {'_id': ref_user_id}
    try:
        user_db.insert_one(user)
        return True
    except DuplicateKeyError:
        return False
    

async def get_referal_all_users(user_id):
    user_db = mydb[str(user_id)]
    return user_db.find()
    
async def get_referal_users_count(user_id):
    user_db = mydb[str(user_id)]
    count = user_db.count_documents({})
    return count
    

async def delete_all_referal_users(user_id):
    user_db = mydb[str(user_id)]
    user_db.delete_many({}) 

default_setgs = {
    'button': BUTTON_MODE,
    'file_secure': PROTECT_CONTENT,
    'imdb': IMDB,
    'spell_check': SPELL_CHECK_REPLY,
    'welcome': MELCOW_NEW_USERS,
    'auto_delete': AUTO_DELETE,
    'auto_ffilter': AUTO_FFILTER,
    'max_btn': MAX_BTN,
    'template': IMDB_TEMPLATE,
    'caption': CUSTOM_FILE_CAPTION,
    'shortlink': SHORTLINK_URL,
    'shortlink_api': SHORTLINK_API,
    'is_shortlink': SHORTLINK_MODE,
    'fsub': None,
    'tutorial': TUTORIAL,
    'is_tutorial': IS_TUTORIAL
}


class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.grp = self.db.groups
        self.users = self.db.uersz
        self.bot = self.db.clone_bots
        self.redeem = self.db.redeem_codes          # Separate redeem codes collection
        self.analytics = self.db.search_analytics   # Search analytics collection
        self.notif = self.db.expiry_notifications   # Expiry reminder tracking


    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            file_id=None,
            caption=None,
            message_command=None,
            save=False,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )


    def new_group(self, id, title):
        return dict(
            id = id,
            title = title,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
            settings=default_setgs
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def add_clone_bot(self, bot_id, user_id, bot_token):
        settings = {
            'bot_id': bot_id,
            'bot_token': bot_token,
            'user_id': user_id,
            'url': None,
            'api': None,
            'tutorial': None,
            'update_channel_link': None
        }
        await self.bot.insert_one(settings)

    async def is_clone_exist(self, user_id):
        clone = await self.bot.find_one({'user_id': int(user_id)})
        return bool(clone)

    async def delete_clone(self, user_id):
        await self.bot.delete_many({'user_id': int(user_id)})

    async def get_clone(self, user_id):
        clone_data = await self.bot.find_one({"user_id": user_id})
        return clone_data
            
    async def update_clone(self, user_id, user_data):
        await self.bot.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)

    async def get_bot(self, bot_id):
        bot_data = await self.bot.find_one({"bot_id": bot_id})
        return bot_data
            
    async def update_bot(self, bot_id, bot_data):
        await self.bot.update_one({"bot_id": bot_id}, {"$set": bot_data}, upsert=True)
    
    async def get_all_bots(self):
        return self.bot.find({})
        
    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id':int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})
    

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})


    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        chats = self.grp.find({'chat_status.is_disabled': True})
        b_chats = [chat['id'] async for chat in chats]
        b_users = [user['id'] async for user in users]
        return b_users, b_chats
    


    async def add_chat(self, chat, title):
        # Use upsert to prevent duplicate group entries in DB
        existing = await self.grp.find_one({'id': int(chat)})
        if existing:
            # Already exists, just update title in case it changed
            await self.grp.update_one({'id': int(chat)}, {'$set': {'title': title}})
        else:
            chat_doc = self.new_group(chat, title)
            await self.grp.insert_one(chat_doc)
    

    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')
    

    async def re_enable_chat(self, id):
        chat_status=dict(
            is_disabled=False,
            reason="",
            )
        await self.grp.update_one({'id': int(id)}, {'$set': {'chat_status': chat_status}})
        
    async def update_settings(self, id, settings):
        await self.grp.update_one({'id': int(id)}, {'$set': {'settings': settings}})
        
    
    async def get_settings(self, id):
        chat = await self.grp.find_one({'id':int(id)})
        if chat:
            return chat.get('settings', default_setgs)
        return default_setgs
    

    async def disable_chat(self, chat, reason="No Reason"):
        chat_status=dict(
            is_disabled=True,
            reason=reason,
            )
        await self.grp.update_one({'id': int(chat)}, {'$set': {'chat_status': chat_status}})
    

    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count
    

    async def get_all_chats(self):
        return self.grp.find({})


    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']

    async def get_user(self, user_id):
        user_data = await self.users.find_one({"id": user_id})
        return user_data
            
    async def update_user(self, user_data):
        await self.users.update_one({"id": user_data["id"]}, {"$set": user_data}, upsert=True)

    async def has_premium_access(self, user_id):
        user_data = await self.get_user(user_id)
        if user_data:
            expiry_time = user_data.get("expiry_time")
            if expiry_time is None:
                # User previously used the free trial, but it has ended.
                return False
            elif isinstance(expiry_time, datetime.datetime) and datetime.datetime.now() <= expiry_time:
                return True
            else:
                await self.users.update_one({"id": user_id}, {"$set": {"expiry_time": None}})
        return False
    
    async def check_remaining_usage(self, userid):
        user_id = userid
        user_data = await self.get_user(user_id)        
        expiry_time = user_data.get("expiry_time")
        # Calculate remaining time
        remaining_time = expiry_time - datetime.datetime.now()
        return remaining_time

    # Backward compat alias — old typo wala naam
    async def check_remaining_uasge(self, userid):
        return await self.check_remaining_usage(userid)

    async def get_free_trial_status(self, user_id):
        user_data = await self.get_user(user_id)
        if user_data:
            return user_data.get("has_free_trial", False)
        return False

    async def give_free_trail(self, userid):        
        user_id = userid
        seconds = 5*60         
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        user_data = {"id": user_id, "expiry_time": expiry_time, "has_free_trial": True}
        await self.users.update_one({"id": user_id}, {"$set": user_data}, upsert=True)
    
    
    async def all_premium_users(self):
        count = await self.users.count_documents({
        "expiry_time": {"$gt": datetime.datetime.now()}
        })
        return count


    # ── REDEEM CODE SYSTEM ──────────────────────────────────────────
    async def save_redeem_code(self, code: str, plan_type: int, duration: str, expiry_hours: int = 48):
        """Save a new redeem code to DB"""
        import datetime
        code_data = {
            "code": code,
            "plan_type": plan_type,       # 1=Bronze, 2=Gold, 3=Diamond
            "duration": duration,          # e.g. 10day, 10week, 1year
            "used": False,
            "used_by": None,
            "created_at": datetime.datetime.now(),
            "expires_at": datetime.datetime.now() + datetime.timedelta(hours=expiry_hours)
        }
        await self.redeem.update_one({"code": code}, {"$set": code_data}, upsert=True)

    async def get_redeem_code(self, code: str):
        """Get redeem code info"""
        return await self.redeem.find_one({"code": code})

    async def mark_redeem_used(self, code: str, user_id: int):
        """Mark code as used by user"""
        import datetime
        await self.redeem.update_one(
            {"code": code},
            {"$set": {"used": True, "used_by": user_id, "used_at": datetime.datetime.now()}}
        )

    async def get_user_redeem_today(self, user_id: int) -> int:
        """Count how many redeem codes this user has used today"""
        import datetime
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = await self.redeem.count_documents({
            "used_by": user_id,
            "used": True,
            "used_at": {"$gte": today_start}
        })
        return count

    async def delete_inactive_chats(self, bot) -> int:
        """Check all saved chats - delete ones where bot is kicked/blocked"""
        import asyncio
        chats = self.grp.find({})
        deleted = 0
        async for chat in chats:
            try:
                await bot.get_chat(chat["id"])
            except Exception:
                await self.grp.delete_one({"id": chat["id"]})
                deleted += 1
                await asyncio.sleep(0.3)
        return deleted

    async def set_thumbnail(self, id, file_id):
        await self.col.update_one({'id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('file_id', None)

    async def set_caption(self, id, caption):
        await self.col.update_one({'id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('caption', None)

    async def set_msg_command(self, id, com):
        await self.col.update_one({'id': int(id)}, {'$set': {'message_command': com}})

    async def get_msg_command(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('message_command', None)

    async def set_save(self, id, save):
        await self.col.update_one({'id': int(id)}, {'$set': {'save': save}})

    async def get_save(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('save', False) 
    

    # ── SEARCH ANALYTICS ───────────────────────────────────────────
    async def track_search(self, query: str):
        """Search query ko analytics mein track karo"""
        q = query.strip().lower()[:100]
        if not q:
            return
        await self.analytics.update_one(
            {"query": q},
            {"$inc": {"count": 1}, "$set": {"last_searched": datetime.datetime.now()}},
            upsert=True
        )

    async def get_top_searches(self, limit: int = 10):
        """Top searched queries return karo"""
        cursor = self.analytics.find({}).sort("count", -1).limit(limit)
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def clear_analytics(self):
        """Saari analytics delete karo"""
        await self.analytics.delete_many({})

    # ── PREMIUM EXPIRY REMINDER ─────────────────────────────────────
    async def get_expiring_soon(self, hours: int = 24):
        """Users jo next N hours mein expire honge"""
        now = datetime.datetime.now()
        soon = now + datetime.timedelta(hours=hours)
        users = []
        async for u in self.users.find({
            "expiry_time": {"$gt": now, "$lte": soon}
        }):
            users.append(u)
        return users

    async def mark_expiry_notified(self, user_id: int):
        """Mark that expiry reminder was sent"""
        await self.users.update_one(
            {"id": user_id},
            {"$set": {"expiry_notified": True}}
        )

    async def clear_expiry_notified(self, user_id: int):
        """Clear the notification flag (reset after expiry)"""
        await self.users.update_one(
            {"id": user_id},
            {"$set": {"expiry_notified": False}}
        )

    # ── MAINTENANCE MODE ────────────────────────────────────────────
    async def get_maintenance_msg(self) -> str:
        """Get custom maintenance message"""
        doc = await self.col.find_one({"_id": "maintenance_msg"})
        return doc.get("msg", "🔧 Bot abhi maintenance pe hai. Thoda wait karo!") if doc else "🔧 Bot abhi maintenance pe hai. Thoda wait karo!"

    async def set_maintenance_msg(self, msg: str):
        """Set custom maintenance message"""
        await self.col.update_one(
            {"_id": "maintenance_msg"},
            {"$set": {"msg": msg}},
            upsert=True
        )

    # ── CLEANUP REDEEM CODES ────────────────────────────────────────
    async def cleanup_expired_codes(self) -> int:
        """Expired aur used redeem codes delete karo"""
        import datetime as dt
        result = await self.redeem.delete_many({
            "$or": [
                {"expires_at": {"$lt": dt.datetime.now()}},
                {"used": True}
            ]
        })
        return result.deleted_count

    async def get_all_codes_count(self) -> dict:
        """Redeem codes ka summary"""
        total   = await self.redeem.count_documents({})
        used    = await self.redeem.count_documents({"used": True})
        active  = await self.redeem.count_documents({"used": False, "expires_at": {"$gt": datetime.datetime.now()}})
        expired = await self.redeem.count_documents({"expires_at": {"$lt": datetime.datetime.now()}, "used": False})
        return {"total": total, "used": used, "active": active, "expired": expired}


db = Database(USER_DB_URI, DATABASE_NAME)
