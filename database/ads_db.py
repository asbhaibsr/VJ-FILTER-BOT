# Don't Remove Credit @VJ_Bots
# Ads Database - MongoDB store for bot ads system

from pymongo import MongoClient
from info import DATABASE_URI, DATABASE_NAME
import datetime

_client = MongoClient(DATABASE_URI)
_db     = _client[DATABASE_NAME]
ads_col = _db["bot_ads"]

def _now():
    return datetime.datetime.utcnow()

def _expiry(duration_str: str) -> datetime.datetime:
    """Parse '1week'/'1month'/'1year' -> datetime"""
    d = duration_str.lower().strip()
    now = _now()
    if "year" in d:
        n = int(''.join(filter(str.isdigit, d)) or 1)
        return now + datetime.timedelta(days=365 * n)
    elif "month" in d:
        n = int(''.join(filter(str.isdigit, d)) or 1)
        return now + datetime.timedelta(days=30 * n)
    elif "week" in d:
        n = int(''.join(filter(str.isdigit, d)) or 1)
        return now + datetime.timedelta(weeks=n)
    elif "day" in d:
        n = int(''.join(filter(str.isdigit, d)) or 1)
        return now + datetime.timedelta(days=n)
    else:
        return now + datetime.timedelta(weeks=1)


def add_ad(title: str, post_text_or_link: str, image, image_type: str, duration: str) -> str:
    """Add new ad. Returns the ad_id (bot start parameter)."""
    import secrets
    ad_id = secrets.token_hex(6)
    doc = {
        "_id":        ad_id,
        "title":      title,
        "content":    post_text_or_link,
        "image":      image,          # file_id or URL or None
        "image_type": image_type,     # "file_id", "url", or None
        "expires":    _expiry(duration),
        "created":    _now(),
        "clicks":     0,
    }
    ads_col.insert_one(doc)
    return ad_id


def get_ad(ad_id: str) -> dict | None:
    doc = ads_col.find_one({"_id": ad_id})
    if doc and doc["expires"] > _now():
        return doc
    return None


def get_active_ad() -> dict | None:
    """Get one random active ad for showing in results."""
    import random
    now = _now()
    active = list(ads_col.find({"expires": {"$gt": now}}))
    if not active:
        return None
    ad = random.choice(active)
    ads_col.update_one({"_id": ad["_id"]}, {"$inc": {"clicks": 0}})
    return ad


def delete_ad(ad_id: str) -> bool:
    res = ads_col.delete_one({"_id": ad_id})
    return res.deleted_count > 0


def list_ads() -> list:
    now = _now()
    return list(ads_col.find({"expires": {"$gt": now}}))


def increment_click(ad_id: str):
    ads_col.update_one({"_id": ad_id}, {"$inc": {"clicks": 1}})
