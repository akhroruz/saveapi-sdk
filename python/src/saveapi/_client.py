from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Optional

import httpx

from .errors import SaveAPIError
from .types import Detection, DownloadResult, YouTubeInfo, YouTubeLink, YouTubeQuality

DEFAULT_BASE_URL = "https://api.saveapi.org"
#: Social links resolve in 1–10 s; a slow source can take up to ~30 s on our side.
DEFAULT_TIMEOUT = 45.0
#: Longest ``Retry-After`` the client is willing to sleep through on 429.
MAX_RATE_LIMIT_WAIT = 60.0

try:
    from importlib.metadata import version as _version

    __version__ = _version("saveapi")
except Exception:  # pragma: no cover - running from a source tree
    __version__ = "0.0.0"


def _key(api_key: Optional[str]) -> str:
    key = api_key or os.environ.get("SAVEAPI_KEY")
    if not key:
        raise ValueError(
            "No API key. Pass api_key=... or set SAVEAPI_KEY. "
            "Get one free at https://saveapi.org/en/signup/"
        )
    return key


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for name, value in params.items():
        if value is None:
            continue
        out[name] = ("true" if value else "false") if isinstance(value, bool) else value
    return out


def _error(response: httpx.Response) -> SaveAPIError:
    code, message = "HTTP_ERROR", response.reason_phrase or "Request failed"
    try:
        body = response.json()
        error = body.get("error") or {}
        code = error.get("code") or code
        message = error.get("message") or message
    except ValueError:
        pass
    retry_after = response.headers.get("Retry-After")
    return SaveAPIError(
        code, message, response.status_code,
        float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else None,
    )


def _delay(error: SaveAPIError, attempt: int) -> Optional[float]:
    """Seconds to wait before retrying, or ``None`` to give up."""
    if error.code == "RATE_LIMITED":
        wait = error.retry_after if error.retry_after is not None else 5.0
        return wait if wait <= MAX_RATE_LIMIT_WAIT else None
    if error.retryable:
        return min(1.0 * (2 ** attempt), 8.0)
    return None


class _Base:
    def __init__(self, api_key: Optional[str], base_url: str, max_retries: int):
        self._headers = {
            "Authorization": f"Bearer {_key(api_key)}",
            "User-Agent": f"saveapi-python/{__version__}",
            "Accept": "application/json",
        }
        self._base_url = base_url.rstrip("/")
        self.max_retries = max_retries


class SaveAPI(_Base):
    """Synchronous client for https://api.saveapi.org.

    >>> from saveapi import SaveAPI
    >>> api = SaveAPI()                      # reads SAVEAPI_KEY
    >>> post = api.download("https://www.tiktok.com/@zachking/video/6768504823336815877")
    >>> post["medias"][0]["url"]

    Args:
        api_key: Your ``sk_live_...`` key. Defaults to ``$SAVEAPI_KEY``.
        max_retries: How many times to retry ``UPSTREAM_TIMEOUT`` /
            ``UPSTREAM_ERROR`` / ``RATE_LIMITED``. Final errors (private,
            deleted, unsupported) are never retried.
        timeout: Per-request timeout in seconds.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        max_retries: int = 1,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.Client] = None,
    ):
        super().__init__(api_key, base_url, max_retries)
        self._http = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "SaveAPI":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _get(self, path: str, **params: Any) -> Any:
        attempt = 0
        while True:
            response = self._http.get(self._base_url + path, params=_clean(params), headers=self._headers)
            if response.is_success:
                return response.json()
            error = _error(response)
            wait = _delay(error, attempt) if attempt < self.max_retries else None
            if wait is None:
                raise error
            time.sleep(wait)
            attempt += 1

    # ── Media ──────────────────────────────────────────────────────────────

    def download(self, url: str, *, full_meta: bool = False, limit_mb: Optional[float] = None) -> DownloadResult:
        """Resolve any supported post link (platform detected from the URL).

        ``full_meta=True`` adds likes, location and music on Instagram (~+0.3 s,
        same price). ``limit_mb`` skips renditions above that size where the
        platform reports sizes.
        """
        return self._get("/v1/download", url=url, full_meta=full_meta or None, limit_mb=limit_mb)

    def platform(self, platform: str, url: str, *, full_meta: bool = False,
                 limit_mb: Optional[float] = None) -> DownloadResult:
        """Resolve through one platform's endpoint, e.g. ``platform("tiktok", url)``."""
        return self._get(f"/v1/{platform}", url=url, full_meta=full_meta or None, limit_mb=limit_mb)

    def youtube_info(self, url: str) -> YouTubeInfo:
        """Title, duration and the qualities a YouTube video offers (2 credits)."""
        return self._get("/v1/youtube/info", url=url)

    def youtube_create(self, url: str, quality: YouTubeQuality = "720p") -> YouTubeLink:
        """A short-lived download link for one quality (10 credits).

        Video qualities are H.264 MP4 144p–1080p; ``mp3`` and ``m4a`` are audio.
        """
        return self._get("/v1/youtube/create", url=url, quality=quality)

    def instagram_profile(self, username: Optional[str] = None, *, url: Optional[str] = None) -> dict:
        """Public profile by username (``natgeo`` or ``@natgeo``) or profile link (3 credits)."""
        if not username and not url:
            raise ValueError("Pass a username or a profile url")
        return self._get("/v1/instagram/profile", username=username, url=url)

    # ── Free calls ─────────────────────────────────────────────────────────

    def detect(self, url: str) -> Detection:
        """Which platform a link belongs to. Free."""
        return self._get("/v1/detect", url=url)

    def platforms(self) -> dict:
        """Supported platforms and their endpoints. Free."""
        return self._get("/v1/platforms")

    def me(self) -> dict:
        """Key, plan and credit balance. Free."""
        return self._get("/v1/me")

    def usage(self, days: int = 30) -> dict:
        """Daily usage for the last ``days`` (1–180). Free."""
        return self._get("/v1/usage", days=days)


class AsyncSaveAPI(_Base):
    """``asyncio`` twin of :class:`SaveAPI` — same methods, awaitable.

    >>> async with AsyncSaveAPI() as api:
    ...     post = await api.download(url)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        max_retries: int = 1,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        super().__init__(api_key, base_url, max_retries)
        self._http = http_client or httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncSaveAPI":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def _get(self, path: str, **params: Any) -> Any:
        attempt = 0
        while True:
            response = await self._http.get(self._base_url + path, params=_clean(params), headers=self._headers)
            if response.is_success:
                return response.json()
            error = _error(response)
            wait = _delay(error, attempt) if attempt < self.max_retries else None
            if wait is None:
                raise error
            await asyncio.sleep(wait)
            attempt += 1

    async def download(self, url: str, *, full_meta: bool = False,
                       limit_mb: Optional[float] = None) -> DownloadResult:
        return await self._get("/v1/download", url=url, full_meta=full_meta or None, limit_mb=limit_mb)

    async def platform(self, platform: str, url: str, *, full_meta: bool = False,
                       limit_mb: Optional[float] = None) -> DownloadResult:
        return await self._get(f"/v1/{platform}", url=url, full_meta=full_meta or None, limit_mb=limit_mb)

    async def youtube_info(self, url: str) -> YouTubeInfo:
        return await self._get("/v1/youtube/info", url=url)

    async def youtube_create(self, url: str, quality: YouTubeQuality = "720p") -> YouTubeLink:
        return await self._get("/v1/youtube/create", url=url, quality=quality)

    async def instagram_profile(self, username: Optional[str] = None, *, url: Optional[str] = None) -> dict:
        if not username and not url:
            raise ValueError("Pass a username or a profile url")
        return await self._get("/v1/instagram/profile", username=username, url=url)

    async def detect(self, url: str) -> Detection:
        return await self._get("/v1/detect", url=url)

    async def platforms(self) -> dict:
        return await self._get("/v1/platforms")

    async def me(self) -> dict:
        return await self._get("/v1/me")

    async def usage(self, days: int = 30) -> dict:
        return await self._get("/v1/usage", days=days)
