# saveapi SDKs — social media downloader API clients

Official clients for **[saveapi.org](https://saveapi.org/)**: one REST API to download videos, photos and audio from **Instagram, TikTok, YouTube, Facebook, X (Twitter), Pinterest, Likee, Snapchat, Threads, VK, Rutube, 9GAG and Twitch**. Send a public post link, get back direct media URLs and metadata in one JSON shape.

| Language | Package | Install | Source |
|---|---|---|---|
| Python 3.9+ | [`saveapi`](https://pypi.org/project/saveapi/) | `pip install saveapi` | [`python/`](python/) |
| JavaScript / TypeScript | [`saveapi`](https://www.npmjs.com/package/saveapi) | `npm install saveapi` | [`js/`](js/) |

Get a free key (1,000 credits, no card): <https://saveapi.org/en/signup/> · Docs: <https://saveapi.org/en/docs/> · Pricing: <https://saveapi.org/en/pricing/>

## Python

```python
from saveapi import SaveAPI

api = SaveAPI()  # reads SAVEAPI_KEY
post = api.download("https://www.tiktok.com/@zachking/video/6768504823336815877")
print(post["medias"][0]["url"])
```

## JavaScript / TypeScript

```ts
import { SaveAPI } from "saveapi";

const api = new SaveAPI(); // reads SAVEAPI_KEY
const post = await api.download("https://www.instagram.com/reel/DdwXSSkMvJz/");
console.log(post.medias[0].url);
```

## What you get back

```json
{
  "success": true,
  "platform": "tiktok",
  "type": "video",
  "medias": [{ "type": "video", "url": "https://v16m.tiktokcdn-us.com/...", "ext": "mp4", "size_mb": 4.19, "watermark": false }],
  "meta": { "title": "...", "author": "Zach King", "duration": 18, "views": 2382320428 },
  "credits": { "spent": 1.5, "remaining": 99988.5 }
}
```

The same shape for every platform. Errors carry a stable `error.code` (`PRIVATE_CONTENT`, `MEDIA_NOT_FOUND`, `UPSTREAM_TIMEOUT`, …); both clients retry only the codes a retry can fix.

## Examples

- [`examples/python/download.py`](examples/python/download.py) — resolve a link and stream the file to disk
- [`examples/python/telegram_bot.py`](examples/python/telegram_bot.py) — a Telegram downloader bot in 50 lines ([guide](https://saveapi.org/en/guides/telegram-bot/))
- [`examples/node/download.mjs`](examples/node/download.mjs) — the same in Node.js
- [`examples/curl/download.sh`](examples/curl/download.sh) — no client at all

More walkthroughs: [Python](https://saveapi.org/en/guides/python/) · [Node.js](https://saveapi.org/en/guides/nodejs/) · [PHP](https://saveapi.org/en/guides/php/) · [Go](https://saveapi.org/en/guides/go/) · [n8n](https://saveapi.org/en/guides/n8n/) · [TikTok without watermark](https://saveapi.org/en/guides/no-watermark/) · [YouTube to MP3](https://saveapi.org/en/guides/youtube-mp3-api/)

## Supported platforms

Instagram (posts, reels, stories, profiles) · TikTok (video, photo slideshows, no watermark) · YouTube (144p–1080p, mp3, m4a) · Facebook · X / Twitter · Pinterest · Likee · Snapchat · Threads · VK · Rutube · 9GAG · Twitch clips — details per platform: <https://saveapi.org/en/platforms/>

## Support

Questions and bugs: open an issue here, or write to hello@saveapi.org.

## License

MIT
