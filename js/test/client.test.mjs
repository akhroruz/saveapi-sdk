import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";

import { SaveAPI, SaveAPIError } from "../dist/esm/index.js";

const OK = {
  success: true, platform: "tiktok", type: "video", source_url: "https://t/1", video_id: "1",
  medias: [{ type: "video", url: "https://cdn/x.mp4", ext: "mp4", quality: null, width: 0, height: 0, size_mb: 1, watermark: false }],
  music: null, meta: {}, credits: { spent: 1.5, remaining: 998.5 },
};

const json = (status, body, headers = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });
const fail = (status, code, headers) => json(status, { success: false, error: { code, message: code.toLowerCase() } }, headers);

function client(answers, options = {}) {
  const calls = [];
  const slept = [];
  const queue = [...answers];
  const api = new SaveAPI({
    apiKey: "sk_test",
    fetch: async (url, init) => {
      calls.push({ url: new URL(url), init });
      return queue.shift();
    },
    sleep: async (ms) => { slept.push(ms); },
    ...options,
  });
  return { api, calls, slept };
}

test("download sends the bearer key and only the set params", async () => {
  const { api, calls } = client([json(200, OK)]);
  const post = await api.download("https://www.tiktok.com/@a/video/1", { fullMeta: true });

  assert.equal(post.medias[0].url, "https://cdn/x.mp4");
  assert.equal(calls[0].url.pathname, "/v1/download");
  assert.deepEqual(Object.fromEntries(calls[0].url.searchParams), { url: "https://www.tiktok.com/@a/video/1", full_meta: "true" });
  assert.equal(calls[0].init.headers.Authorization, "Bearer sk_test");
  assert.match(calls[0].init.headers["User-Agent"], /^saveapi-js\//);
});

test("a final error is thrown without retrying", async () => {
  const { api, calls, slept } = client([fail(403, "PRIVATE_CONTENT")], { maxRetries: 3 });
  await assert.rejects(api.download("https://t/1"), (error) => {
    assert.ok(error instanceof SaveAPIError);
    assert.equal(error.code, "PRIVATE_CONTENT");
    assert.equal(error.status, 403);
    assert.equal(error.retryable, false);
    return true;
  });
  assert.equal(calls.length, 1);
  assert.deepEqual(slept, []);
});

test("upstream timeout is retried once by default", async () => {
  const { api, slept } = client([fail(504, "UPSTREAM_TIMEOUT"), json(200, OK)]);
  const post = await api.download("https://t/1");
  assert.equal(post.success, true);
  assert.deepEqual(slept, [1000]);
});

test("retries are bounded", async () => {
  const { api, calls } = client([fail(502, "UPSTREAM_ERROR"), fail(502, "UPSTREAM_ERROR"), fail(502, "UPSTREAM_ERROR")], { maxRetries: 2 });
  await assert.rejects(api.download("https://t/1"), SaveAPIError);
  assert.equal(calls.length, 3);
});

test("rate limit waits for Retry-After", async () => {
  const { api, slept } = client([fail(429, "RATE_LIMITED", { "Retry-After": "7" }), json(200, OK)]);
  await api.download("https://t/1");
  assert.deepEqual(slept, [7000]);
});

test("quota exceeded is final", async () => {
  const { api } = client([fail(429, "QUOTA_EXCEEDED")]);
  await assert.rejects(api.download("https://t/1"), (error) => error.code === "QUOTA_EXCEEDED" && !error.retryable);
});

test("a non-JSON error keeps the HTTP status", async () => {
  const { api } = client([new Response("<html>bad gateway</html>", { status: 502 })]);
  await assert.rejects(api.me(), (error) => error.status === 502 && error.code === "HTTP_ERROR");
});

test("youtubeCreate and instagramProfile build the right query", async () => {
  const { api, calls } = client([json(200, { success: true }), json(200, { success: true }), json(200, { success: true })]);
  await api.youtubeCreate("https://youtu.be/x", "mp3");
  await api.instagramProfile("@natgeo");
  await api.instagramProfile({ url: "https://www.instagram.com/natgeo/" });

  assert.deepEqual(Object.fromEntries(calls[0].url.searchParams), { url: "https://youtu.be/x", quality: "mp3" });
  assert.deepEqual(Object.fromEntries(calls[1].url.searchParams), { username: "@natgeo" });
  assert.deepEqual(Object.fromEntries(calls[2].url.searchParams), { url: "https://www.instagram.com/natgeo/" });
});

test("missing key explains where to get one", () => {
  const saved = process.env.SAVEAPI_KEY;
  delete process.env.SAVEAPI_KEY;
  try {
    assert.throws(() => new SaveAPI(), /saveapi\.org/);
  } finally {
    if (saved !== undefined) process.env.SAVEAPI_KEY = saved;
  }
});

test("the CommonJS build loads with require()", () => {
  const require = createRequire(import.meta.url);
  const cjs = require("../dist/cjs/index.cjs");
  assert.equal(typeof cjs.SaveAPI, "function");
  assert.equal(cjs.default, cjs.SaveAPI);
});
