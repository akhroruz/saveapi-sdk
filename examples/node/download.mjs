// Resolve a post link and save the first media file to disk.
//
//   npm install saveapi
//   SAVEAPI_KEY=sk_live_... node download.mjs "https://www.instagram.com/reel/DdwXSSkMvJz/"

import { createWriteStream } from "node:fs";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

import { SaveAPI, SaveAPIError } from "saveapi";

const api = new SaveAPI();
const url = process.argv[2];

try {
  const post = await api.download(url);
  const media = post.medias[0];
  const name = `${post.platform}-${post.video_id ?? "media"}.${media.ext ?? "bin"}`;

  // The URL points at the platform's CDN: stream it to disk.
  const response = await fetch(media.url);
  if (!response.ok) throw new Error(`CDN answered ${response.status}`);
  await pipeline(Readable.fromWeb(response.body), createWriteStream(name));

  console.log(`saved ${name} (${post.credits.spent} credits spent, ${post.credits.remaining} left)`);
} catch (error) {
  if (error instanceof SaveAPIError) {
    console.error(`${error.code}: ${error.message}`);
    process.exit(1);
  }
  throw error;
}
