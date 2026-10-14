/**
 * JavaScript / TypeScript client for saveapi.org — download media from
 * Instagram, TikTok, YouTube, Facebook, X, Pinterest, Likee, Snapchat,
 * Threads, VK, Rutube, 9GAG and Twitch with one API.
 *
 * Docs: https://saveapi.org/en/docs/
 *
 * Works anywhere with a global `fetch`: Node 18+, Deno, Bun, Cloudflare
 * Workers, browsers (keep your key on the server).
 */

export const VERSION = "0.1.0";
export const DEFAULT_BASE_URL = "https://api.saveapi.org";

/** Codes a retry can fix. Everything else is a final answer. */
export const RETRYABLE_CODES: ReadonlySet<string> = new Set([
  "UPSTREAM_TIMEOUT",
  "UPSTREAM_ERROR",
  "RATE_LIMITED",
]);

/** Longest `Retry-After` the client sleeps through on 429, in seconds. */
const MAX_RATE_LIMIT_WAIT = 60;

// ── Response types ──────────────────────────────────────────────────────────

export type Credits = { spent: number; remaining: number | null };

export type Media = {
  type: "video" | "image" | "audio";
  url: string;
  ext: string | null;
  quality: string | null;
  width: number | null;
  height: number | null;
  size_mb: number | null;
  watermark: boolean | null;
};

/** A ready rendition the source itself offers (TikTok, VK, Likee). */
export type Format = {
  format: string;
  label: string;
  type: "video" | "audio";
  size_mb: number | null;
  exact: boolean;
  url: string;
  watermark?: boolean | null;
};

export type Meta = Partial<{
  title: string | null;
  text: string | null;
  author: string | null;
  author_url: string | null;
  thumbnail: string | null;
  duration: number | null;
  views: number | null;
  published_at: number | null;
  username: string | null;
  author_avatar: string | null;
  author_verified: boolean | null;
  likes: number | null;
  comments: number | null;
  shares: number | null;
  saves: number | null;
  location: string | null;
  region: string | null;
  music: Record<string, unknown> | null;
}>;

/** `/v1/download` and `/v1/{platform}`. */
export type DownloadResult = {
  success: true;
  platform: string;
  type: string;
  source_url: string;
  video_id: string | null;
  medias: Media[];
  music: Media | null;
  meta: Meta;
  formats?: Format[];
  recommended_format?: string | null;
  credits: Credits;
};

export type YouTubeFormat = {
  quality: string;
  file_size: number | null;
  file_size_str: string | null;
  exact: boolean;
};

export type YouTubeInfo = {
  success: true;
  platform: "youtube";
  source_url: string;
  video_id: string;
  title: string;
  author: string | null;
  duration_seconds: number | null;
  duration_str: string | null;
  thumbnail: string | null;
  is_short: boolean;
  formats: YouTubeFormat[];
  audio_formats: YouTubeFormat[];
  credits: Credits;
};

export type YouTubeQuality = "144p" | "240p" | "360p" | "480p" | "720p" | "1080p" | "mp3" | "m4a";

export type YouTubeLink = {
  success: true;
  platform: "youtube";
  source_url: string;
  video_id: string;
  url: string;
  filename: string;
  quality: string;
  mode: "video" | "audio";
  ext: string;
  file_size: number | null;
  file_size_str: string | null;
  exact: boolean;
  seekable: boolean;
  expires: number;
  title: string;
  duration_seconds: number | null;
  duration_str: string | null;
  thumbnail: string | null;
  credits: Credits;
};

export type Detection = {
  success: true;
  supported: boolean;
  platform: string | null;
  name?: string | null;
  host?: string | null;
  formats?: boolean;
};

export type DownloadOptions = {
  /** Instagram: also return likes, location and music (~+0.3 s, same price). */
  fullMeta?: boolean;
  /** Skip renditions above this size where the platform reports sizes. */
  limitMb?: number;
};

// ── Errors ──────────────────────────────────────────────────────────────────

/** A non-2xx answer. Match on `code` — codes are stable, messages are not. */
export class SaveAPIError extends Error {
  readonly code: string;
  readonly status: number;
  readonly retryAfter: number | null;

  constructor(code: string, message: string, status: number, retryAfter: number | null = null) {
    super(`${code}: ${message}`);
    this.name = "SaveAPIError";
    this.code = code;
    this.status = status;
    this.retryAfter = retryAfter;
  }

  /** True when sending the same request again can succeed. */
  get retryable(): boolean {
    return RETRYABLE_CODES.has(this.code);
  }
}

// ── Client ──────────────────────────────────────────────────────────────────

export type ClientOptions = {
  /** Your `sk_live_...` key. Defaults to `process.env.SAVEAPI_KEY`. */
  apiKey?: string;
  baseUrl?: string;
  /** Retries for UPSTREAM_TIMEOUT / UPSTREAM_ERROR / RATE_LIMITED. Default 1. */
  maxRetries?: number;
  /** Per-request timeout in milliseconds. Default 45 000. */
  timeoutMs?: number;
  /** Custom fetch (tests, proxies). Defaults to the global one. */
  fetch?: typeof fetch;
  /** Custom sleep (tests). */
  sleep?: (ms: number) => Promise<void>;
};

type Params = Record<string, string | number | boolean | null | undefined>;

function envKey(): string | undefined {
  const env = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env;
  return env?.SAVEAPI_KEY;
}

/**
 * ```ts
 * import { SaveAPI } from "saveapi";
 *
 * const api = new SaveAPI({ apiKey: "sk_live_..." });
 * const post = await api.download("https://www.tiktok.com/@zachking/video/6768504823336815877");
 * console.log(post.medias[0].url);
 * ```
 */
export class SaveAPI {
  readonly maxRetries: number;
  private readonly key: string;
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  private readonly fetchImpl: typeof fetch;
  private readonly sleep: (ms: number) => Promise<void>;
  private readonly headers: Record<string, string>;

  constructor(options: ClientOptions = {}) {
    const key = options.apiKey ?? envKey();
    if (!key) {
      throw new Error(
        "No API key. Pass { apiKey } or set SAVEAPI_KEY. Get one free at https://saveapi.org/en/signup/",
      );
    }
    this.key = key;
    this.baseUrl = (options.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.maxRetries = options.maxRetries ?? 1;
    this.timeoutMs = options.timeoutMs ?? 45_000;
    this.fetchImpl = options.fetch ?? globalThis.fetch.bind(globalThis);
    this.sleep = options.sleep ?? ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
    this.headers = { Authorization: `Bearer ${key}`, Accept: "application/json" };
    // Browsers forbid setting User-Agent (and a custom header would force a
    // CORS preflight), so the client identifies itself on servers only.
    if (typeof (globalThis as { window?: unknown }).window === "undefined") {
      this.headers["User-Agent"] = `saveapi-js/${VERSION}`;
    }
  }

  private async get<T>(path: string, params: Params = {}): Promise<T> {
    const query = new URLSearchParams();
    for (const [name, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === false) continue;
      query.set(name, String(value));
    }
    const url = `${this.baseUrl}${path}${query.size ? `?${query}` : ""}`;

    for (let attempt = 0; ; attempt++) {
      const response = await this.fetchImpl(url, {
        headers: this.headers,
        signal: AbortSignal.timeout(this.timeoutMs),
      });
      if (response.ok) return (await response.json()) as T;

      const error = await toError(response);
      const wait = attempt < this.maxRetries ? retryDelay(error, attempt) : null;
      if (wait === null) throw error;
      await this.sleep(wait * 1000);
    }
  }

  /** Resolve any supported post link; the platform is detected from the URL. */
  download(url: string, options: DownloadOptions = {}): Promise<DownloadResult> {
    return this.get("/v1/download", { url, full_meta: options.fullMeta, limit_mb: options.limitMb });
  }

  /** Resolve through one platform's endpoint, e.g. `platform("tiktok", url)`. */
  platform(platform: string, url: string, options: DownloadOptions = {}): Promise<DownloadResult> {
    return this.get(`/v1/${encodeURIComponent(platform)}`, {
      url, full_meta: options.fullMeta, limit_mb: options.limitMb,
    });
  }

  /** Title, duration and the qualities a YouTube video offers (2 credits). */
  youtubeInfo(url: string): Promise<YouTubeInfo> {
    return this.get("/v1/youtube/info", { url });
  }

  /** A short-lived download link for one quality (10 credits). */
  youtubeCreate(url: string, quality: YouTubeQuality = "720p"): Promise<YouTubeLink> {
    return this.get("/v1/youtube/create", { url, quality });
  }

  /** Public profile by username (`natgeo` / `@natgeo`) or `{ url }` (3 credits). */
  instagramProfile(target: string | { url: string }): Promise<Record<string, unknown>> {
    return this.get(
      "/v1/instagram/profile",
      typeof target === "string" ? { username: target } : { url: target.url },
    );
  }

  /** Which platform a link belongs to. Free. */
  detect(url: string): Promise<Detection> {
    return this.get("/v1/detect", { url });
  }

  /** Supported platforms and their endpoints. Free. */
  platforms(): Promise<Record<string, unknown>> {
    return this.get("/v1/platforms");
  }

  /** Key, plan and credit balance. Free. */
  me(): Promise<Record<string, unknown>> {
    return this.get("/v1/me");
  }

  /** Daily usage for the last `days` (1–180). Free. */
  usage(days = 30): Promise<Record<string, unknown>> {
    return this.get("/v1/usage", { days });
  }
}

async function toError(response: Response): Promise<SaveAPIError> {
  let code = "HTTP_ERROR";
  let message = response.statusText || "Request failed";
  try {
    const body = (await response.json()) as { error?: { code?: string; message?: string } };
    code = body.error?.code ?? code;
    message = body.error?.message ?? message;
  } catch {
    // Not JSON (a proxy error page, for example) — keep the HTTP status.
  }
  const header = response.headers.get("Retry-After");
  const retryAfter = header !== null && /^\d+(\.\d+)?$/.test(header) ? Number(header) : null;
  return new SaveAPIError(code, message, response.status, retryAfter);
}

/** Seconds to wait before retrying, or `null` to give up. */
function retryDelay(error: SaveAPIError, attempt: number): number | null {
  if (error.code === "RATE_LIMITED") {
    const wait = error.retryAfter ?? 5;
    return wait <= MAX_RATE_LIMIT_WAIT ? wait : null;
  }
  if (error.retryable) return Math.min(2 ** attempt, 8);
  return null;
}

export default SaveAPI;
