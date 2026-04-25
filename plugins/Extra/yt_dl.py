# Don't Remove Credit @VJ_Bots
# YouTube Song & Video Downloader
# Commands: /song <name>  |  /video <link or name>  |  /mp4 <link or name>

import os, asyncio, re
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from info import CHNL_LNK
from yt_dlp import YoutubeDL

def _sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name)

def _dur_sec(dur_str: str) -> int:
    """'3:45' or '1:02:30' -> seconds"""
    try:
        parts = [int(x) for x in str(dur_str).split(":")]
        if len(parts) == 3:
            return parts[0]*3600 + parts[1]*60 + parts[2]
        elif len(parts) == 2:
            return parts[0]*60 + parts[1]
        return int(parts[0])
    except Exception:
        return 0


# ── /song  /mp3 ────────────────────────────────────────────────────
@Client.on_message(filters.command(["song", "mp3"]))
async def song_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>🎵 Song ka naam do!\n\nExample: <code>/song Kesariya</code></b>",
            parse_mode=enums.ParseMode.HTML
        )

    query = " ".join(message.command[1:])
    status = await message.reply_text(
        f"🔍 <b>Searching:</b> <code>{query}</code>...",
        parse_mode=enums.ParseMode.HTML
    )

    search_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch1",
        "outtmpl": "/tmp/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    loop = asyncio.get_event_loop()
    try:
        await status.edit("<b>⬇️ Downloading song...</b>", parse_mode=enums.ParseMode.HTML)

        def _download():
            with YoutubeDL(search_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                if "entries" in info:
                    info = info["entries"][0]
                return info

        info = await loop.run_in_executor(None, _download)

        title    = info.get("title", query)[:50]
        duration = info.get("duration", 0)
        uploader = info.get("uploader", "Unknown")
        thumb_url = info.get("thumbnail")
        vid_id   = info.get("id", "")
        audio_file = f"/tmp/{vid_id}.mp3"

        # Thumbnail download
        thumb_file = None
        if thumb_url:
            try:
                import requests
                r = requests.get(thumb_url, timeout=10)
                thumb_file = f"/tmp/{vid_id}.jpg"
                with open(thumb_file, "wb") as tf:
                    tf.write(r.content)
            except Exception:
                thumb_file = None

        caption = (
            f"🎵 <b>{title}</b>\n"
            f"👤 {uploader}\n"
            f"📡 <a href=\"{CHNL_LNK}\">Updates Channel</a>"
        )

        await status.delete()
        await message.reply_audio(
            audio=audio_file,
            caption=caption,
            duration=duration,
            performer=uploader,
            title=title,
            thumb=thumb_file,
            parse_mode=enums.ParseMode.HTML
        )

    except Exception as e:
        await status.edit(
            f"<b>❌ Error aaya!\n<code>{str(e)[:200]}</code></b>",
            parse_mode=enums.ParseMode.HTML
        )
    finally:
        for f in [f"/tmp/{vid_id}.mp3", f"/tmp/{vid_id}.jpg"] if "vid_id" in dir() else []:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass


# ── /video  /mp4 ───────────────────────────────────────────────────
@Client.on_message(filters.command(["video", "mp4"]))
async def video_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>🎬 YouTube link ya naam do!\n\n"
            "Examples:\n"
            "<code>/video https://youtu.be/xxxxx</code>\n"
            "<code>/mp4 Avengers Endgame trailer</code></b>",
            parse_mode=enums.ParseMode.HTML
        )

    query = " ".join(message.command[1:])
    is_url = query.startswith("http") or "youtu" in query

    status = await message.reply_text(
        f"🔍 <b>{'Processing' if is_url else 'Searching'}:</b> <code>{query[:60]}</code>...",
        parse_mode=enums.ParseMode.HTML
    )

    vid_opts = {
        "format": "best[height<=720]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "outtmpl": "/tmp/%(id)s.%(ext)s",
        "default_search": "ytsearch1",
        "geo_bypass": True,
        "nocheckcertificate": True,
    }

    loop = asyncio.get_event_loop()
    vid_id = None
    try:
        await status.edit("<b>⬇️ Downloading video...</b>", parse_mode=enums.ParseMode.HTML)

        def _download():
            src = query if is_url else f"ytsearch1:{query}"
            with YoutubeDL(vid_opts) as ydl:
                info = ydl.extract_info(src, download=True)
                if "entries" in info:
                    info = info["entries"][0]
                return info

        info = await loop.run_in_executor(None, _download)

        vid_id   = info.get("id", "video")
        title    = info.get("title", query)[:60]
        duration = int(info.get("duration", 0))
        uploader = info.get("uploader", "Unknown")
        ext      = info.get("ext", "mp4")
        vid_url  = info.get("webpage_url", "")

        video_file = f"/tmp/{vid_id}.{ext}"

        # Thumbnail
        thumb_url  = info.get("thumbnail")
        thumb_file = None
        if thumb_url:
            try:
                import requests
                r = requests.get(thumb_url, timeout=10)
                thumb_file = f"/tmp/{vid_id}_thumb.jpg"
                with open(thumb_file, "wb") as tf:
                    tf.write(r.content)
            except Exception:
                thumb_file = None

        caption = (
            f"🎬 <b><a href=\"{vid_url}\">{title}</a></b>\n"
            f"👤 {uploader}\n"
            f"📡 <a href=\"{CHNL_LNK}\">Updates Channel</a>"
        )

        await status.delete()
        await message.reply_video(
            video=video_file,
            caption=caption,
            duration=duration,
            thumb=thumb_file,
            supports_streaming=True,
            parse_mode=enums.ParseMode.HTML
        )

    except Exception as e:
        await status.edit(
            f"<b>❌ Download fail hua!\n<code>{str(e)[:200]}</code></b>",
            parse_mode=enums.ParseMode.HTML
        )
    finally:
        for ext2 in ["mp4", "mkv", "webm", "jpg"]:
            f = f"/tmp/{vid_id}.{ext2}" if vid_id else None
            if f and os.path.exists(f):
                try: os.remove(f)
                except Exception: pass
        if vid_id:
            t = f"/tmp/{vid_id}_thumb.jpg"
            if os.path.exists(t):
                try: os.remove(t)
                except Exception: pass
