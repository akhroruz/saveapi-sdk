# saveapi — Python client for saveapi.org

Download videos, photos and audio from **Instagram, TikTok, YouTube, Facebook, X (Twitter), Pinterest, Likee, Snapchat, Threads, VK, Rutube, 9GAG and Twitch** with one API call. Send a public post link, get back direct media URLs and metadata in one JSON shape.

- Docs: <https://saveapi.org/en/docs/>
- Free key (1,000 credits, no card): <https://saveapi.org/en/signup/>
- Pricing: <https://saveapi.org/en/pricing/>

```bash
pip install saveapi
```

## Quick start

```python
from saveapi import SaveAPI

api = SaveAPI("sk_live_...")          # or set SAVEAPI_KEY and call SaveAPI()

post = api.download("https://www.tiktok.com/@zachking/video/6768504823336815877")
print(post["platform"], post["meta"]["title"])
for media in post["medias"]:
    print(media["type"], media["ext"], media["url"])
```

`download()` detects the platform from the link. To call one platform's endpoint directly use `api.platform("instagram", url)`.

## Async

```python
import asyncio
from saveapi import AsyncSaveAPI

async def main():
    async with AsyncSaveAPI() as api:
        post = await api.download("https://www.instagram.com/reel/DdwXSSkMvJz/")
        print(post["medias"][0]["url"])

asyncio.run(main())
```

## YouTube

YouTube is two steps: read the available qualities, then create a link for one of them.

```python
info = api.youtube_info("https://youtu.be/dQw4w9WgXcQ")          # 2 credits
print([f["quality"] for f in info["formats"]])

link = api.youtube_create("https://youtu.be/dQw4w9WgXcQ", "mp3")  # 10 credits
print(link["url"], link["filename"])
```

Video qualities are H.264 MP4 `144p`–`1080p`; `mp3` and `m4a` are audio. The link is short-lived — download it right away.

## Errors

Every failed call raises `SaveAPIError`. Match on `error.code`, not on the message:

```python
from saveapi import SaveAPI, SaveAPIError

try:
    post = api.download(url)
except SaveAPIError as error:
    if error.code in ("PRIVATE_CONTENT", "MEDIA_NOT_FOUND"):
        print("The post is private or gone")      # final answer, costs 0.1 credit
    elif error.code == "QUOTA_EXCEEDED":
        print("Top up at https://saveapi.org/en/dashboard/billing/")
    else:
        raise
```

The client retries only what a retry can fix: `UPSTREAM_TIMEOUT` and `UPSTREAM_ERROR` (once by default, `max_retries=`), and `RATE_LIMITED` after the `Retry-After` delay. Private, deleted and unsupported links are never retried. Full list of codes: <https://saveapi.org/en/docs/#errors>.

## All methods

| Method | Endpoint | Cost |
|---|---|---|
| `download(url, full_meta=False, limit_mb=None)` | `/v1/download` | 1.5 credits |
| `platform(name, url, ...)` | `/v1/{platform}` | 1.5 credits |
| `youtube_info(url)` | `/v1/youtube/info` | 2 credits |
| `youtube_create(url, quality="720p")` | `/v1/youtube/create` | 10 credits |
| `instagram_profile(username=None, url=None)` | `/v1/instagram/profile` | 3 credits |
| `detect(url)` | `/v1/detect` | free |
| `platforms()` | `/v1/platforms` | free |
| `me()` | `/v1/me` | free |
| `usage(days=30)` | `/v1/usage` | free |

Instagram stories cost 5 credits, Rutube 3, and a link the source refuses 0.1. Current prices: <https://saveapi.org/en/pricing/>.

## Guides

- [Telegram downloader bot](https://saveapi.org/en/guides/telegram-bot/)
- [Download social media videos in Python](https://saveapi.org/en/guides/python/)
- [TikTok without watermark](https://saveapi.org/en/guides/no-watermark/)
- [YouTube to MP3 API](https://saveapi.org/en/guides/youtube-mp3-api/)

## License

MIT
