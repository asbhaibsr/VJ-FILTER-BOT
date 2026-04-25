
# Don't Remove Credit @VJ_Bots
# YouTube Song & Video Downloader — Cookies workaround via innertube

import os, asyncio, re
from pyrogram import Client, filters, enums
from pyrogram.types import Message

YT_OPTS_BASE = {
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "socket_timeout": 30,
    "extractor_args": {
        "youtube": {
            "player_client": ["web_creator", "android"],
        }
    },
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 Chrome/90.0 Mobile Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    },
}


# /song /mp3
@Client.on_message(filters.command(["song", "mp3"]))
async def song_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>🎵 Song naam do!\n\nExample: <code>/song Kesariya</code></b>",
            parse_mode=enums.ParseMode.HTML
        )

    query = " ".join(message.command[1:])
    status = await message.reply_text(
        f"🔍 <b>Searching:</b> <code>{query}</code>...",
        parse_mode=enums.ParseMode.HTML
    )

    opts = {
        **YT_OPTS_BASE,
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": "/tmp/%(id)s.%(ext)s",
        "default_search": "ytsearch1",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    vid_id = None
    try:
        from yt_dlp import YoutubeDL
        await status.edit("<b>⬇️ Downloading song...</b>", parse_mode=enums.ParseMode.HTML)

        loop = asyncio.get_event_loop()
        def _dl():
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                if "entries" in info:
                    info = info["entries"][0]
                return info
        info = await loop.run_in_executor(None, _dl)

        vid_id   = info.get("id", "")
        title    = info.get("title", query)[:60]
        duration = int(info.get("duration", 0))
        uploader = info.get("uploader", "Unknown")
        thumb_url = info.get("thumbnail", "")

        thumb_path = None
        if thumb_url:
            try:
                import requests
                r = requests.get(thumb_url, timeout=10)
                thumb_path = f"/tmp/{vid_id}_thumb.jpg"
                open(thumb_path, "wb").write(r.content)
            except: thumb_path = None

        audio_path = f"/tmp/{vid_id}.mp3"
        caption = f"🎵 <b>{title}</b>\n👤 {uploader}"

        await status.delete()
        await message.reply_audio(
            audio=audio_path,
            caption=caption,
            duration=duration,
            performer=uploader,
            title=title,
            thumb=thumb_path,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        err = str(e)
        if "Sign in" in err or "bot" in err.lower():
            msg = "❌ <b>YouTube ne block kiya!\n\nYT-dlp cookies issue hai — server pe cookies.txt set karna hoga.</b>"
        else:
            msg = f"❌ <b>Error:</b> <code>{err[:200]}</code>"
        await status.edit(msg, parse_mode=enums.ParseMode.HTML)
    finally:
        for ext in ["mp3", "m4a", "webm"]:
            p = f"/tmp/{vid_id}.{ext}" if vid_id else None
            if p and os.path.exists(p): 
                try: os.remove(p)
                except: pass
        if vid_id:
            t = f"/tmp/{vid_id}_thumb.jpg"
            if os.path.exists(t):
                try: os.remove(t)
                except: pass


# /video /mp4
@Client.on_message(filters.command(["video", "mp4"]))
async def video_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>🎬 YouTube link ya naam do!\n\n"
            "Example:\n<code>/mp4 https://youtu.be/xxxxx</code>\n"
            "<code>/video Avengers trailer</code></b>",
            parse_mode=enums.ParseMode.HTML
        )

    query = " ".join(message.command[1:])
    is_url = "youtu" in query or query.startswith("http")
    status = await message.reply_text(
        f"🔍 <b>Processing:</b> <code>{query[:60]}</code>...",
        parse_mode=enums.ParseMode.HTML
    )

    opts = {
        **YT_OPTS_BASE,
        "format": "best[height<=720][ext=mp4]/best[height<=720]/best",
        "outtmpl": "/tmp/%(id)s.%(ext)s",
        "default_search": "ytsearch1",
    }

    vid_id = None
    try:
        from yt_dlp import YoutubeDL
        await status.edit("<b>⬇️ Downloading video...</b>", parse_mode=enums.ParseMode.HTML)

        loop = asyncio.get_event_loop()
        def _dl():
            src = query if is_url else f"ytsearch1:{query}"
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(src, download=True)
                if "entries" in info:
                    info = info["entries"][0]
                return info
        info = await loop.run_in_executor(None, _dl)

        vid_id   = info.get("id", "video")
        title    = info.get("title", query)[:60]
        duration = int(info.get("duration", 0))
        uploader = info.get("uploader", "Unknown")
        ext      = info.get("ext", "mp4")
        vid_url  = info.get("webpage_url", "")

        thumb_url  = info.get("thumbnail", "")
        thumb_path = None
        if thumb_url:
            try:
                import requests
                r = requests.get(thumb_url, timeout=10)
                thumb_path = f"/tmp/{vid_id}_thumb.jpg"
                open(thumb_path, "wb").write(r.content)
            except: thumb_path = None

        video_path = f"/tmp/{vid_id}.{ext}"
        caption = f"🎬 <b>{title}</b>\n👤 {uploader}"

        await status.delete()
        await message.reply_video(
            video=video_path,
            caption=caption,
            duration=duration,
            thumb=thumb_path,
            supports_streaming=True,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        err = str(e)
        if "Sign in" in err or "bot" in err.lower():
            msg = "❌ <b>YouTube ne block kiya!\n\nYT-dlp cookies issue hai — server pe cookies.txt set karna hoga.</b>"
        else:
            msg = f"❌ <b>Error:</b> <code>{err[:200]}</code>"
        await status.edit(msg, parse_mode=enums.ParseMode.HTML)
    finally:
        for ext2 in ["mp4", "mkv", "webm"]:
            p = f"/tmp/{vid_id}.{ext2}" if vid_id else None
            if p and os.path.exists(p):
                try: os.remove(p)
                except: pass
        if vid_id:
            t = f"/tmp/{vid_id}_thumb.jpg"
            if os.path.exists(t):
                try: os.remove(t)
                except: pass
