# saveapi — JavaScript / TypeScript client for saveapi.org

Download videos, photos and audio from **Instagram, TikTok, YouTube, Facebook, X (Twitter), Pinterest, Likee, Snapchat, Threads, VK, Rutube, 9GAG and Twitch** with one API call. Send a public post link, get back direct media URLs and metadata in one JSON shape.

- Docs: <https://saveapi.org/en/docs/>
- Free key (1,000 credits, no card): <https://saveapi.org/en/signup/>
- Pricing: <https://saveapi.org/en/pricing/>

```bash
npm install saveapi
```

Zero dependencies. Works anywhere with a global `fetch`: Node 18+, Deno, Bun, Cloudflare Workers. ESM and CommonJS, typed.

## Quick start

```ts
import { SaveAPI } from "saveapi";

const api = new SaveAPI({ apiKey: process.env.SAVEAPI_KEY });

const post = await api.download("https://www.tiktok.com/@zachking/video/6768504823336815877");
console.log(post.platform, post.meta.title);
for (const media of post.medias) console.log(media.type, media.ext, media.url);
```

`download()` detects the platform from the link. To call one platform's endpoint directly use `api.platform("instagram", url)`. CommonJS: `const { SaveAPI } = require("saveapi")`.

## YouTube

```ts
const info = await api.youtubeInfo("https://youtu.be/dQw4w9WgXcQ");         // 2 credits
console.log(info.formats.map((f) => f.quality));

const link = await api.youtubeCreate("https://youtu.be/dQw4w9WgXcQ", "mp3"); // 10 credits
console.log(link.url, link.filename);
```

Video qualities are H.264 MP4 `144p`–`1080p`; `mp3` and `m4a` are audio. The link is short-lived — download it right away.

## Errors

Every failed call throws `SaveAPIError`. Match on `error.code`, not on the message:

```ts
import { SaveAPI, SaveAPIError } from "saveapi";

try {
  const post = await api.download(url);
} catch (error) {
  if (error instanceof SaveAPIError && ["PRIVATE_CONTENT", "MEDIA_NOT_FOUND"].includes(error.code)) {
    console.log("The post is private or gone"); // final answer, costs 0.1 credit
  } else {
    throw error;
  }
}
```

The client retries only what a retry can fix: `UPSTREAM_TIMEOUT` and `UPSTREAM_ERROR` (once by default, `maxRetries`), and `RATE_LIMITED` after the `Retry-After` delay. Private, deleted and unsupported links are never retried. All codes: <https://saveapi.org/en/docs/#errors>.

> Keep your key on the server. Calling the API from a browser exposes `sk_live_...` to anyone who opens dev tools.

## All methods

| Method | Endpoint | Cost |
|---|---|---|
| `download(url, { fullMeta, limitMb })` | `/v1/download` | 1.5 credits |
| `platform(name, url, options)` | `/v1/{platform}` | 1.5 credits |
| `youtubeInfo(url)` | `/v1/youtube/info` | 2 credits |
| `youtubeCreate(url, quality = "720p")` | `/v1/youtube/create` | 10 credits |
| `instagramProfile("natgeo" \| { url })` | `/v1/instagram/profile` | 3 credits |
| `detect(url)` | `/v1/detect` | free |
| `platforms()` | `/v1/platforms` | free |
| `me()` | `/v1/me` | free |
| `usage(days = 30)` | `/v1/usage` | free |

Instagram stories cost 5 credits, Rutube 3, and a link the source refuses 0.1. Current prices: <https://saveapi.org/en/pricing/>.

## Guides

- [Telegram downloader bot](https://saveapi.org/en/guides/telegram-bot/)
- [Download social media videos in Node.js](https://saveapi.org/en/guides/nodejs/)
- [TikTok without watermark](https://saveapi.org/en/guides/no-watermark/)
- [n8n workflow](https://saveapi.org/en/guides/n8n/)

## License

MIT
