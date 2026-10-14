"""Response shapes (``TypedDict``) — the client returns plain dicts.

Field names match https://saveapi.org/en/docs/. Fields the source does not
provide are ``None`` rather than missing.
"""

from __future__ import annotations

from typing import Literal, Optional, TypedDict

from typing_extensions import NotRequired


class Credits(TypedDict):
    spent: float
    remaining: Optional[float]


class Media(TypedDict):
    type: Literal["video", "image", "audio"]
    url: str
    ext: Optional[str]
    quality: Optional[str]
    width: Optional[int]
    height: Optional[int]
    size_mb: Optional[float]
    watermark: Optional[bool]


class Format(TypedDict):
    """A ready rendition the source itself offers (TikTok, VK, Likee)."""

    format: str
    label: str
    type: Literal["video", "audio"]
    size_mb: Optional[float]
    exact: bool
    url: str
    watermark: NotRequired[Optional[bool]]


class Meta(TypedDict, total=False):
    title: Optional[str]
    text: Optional[str]
    author: Optional[str]
    author_url: Optional[str]
    thumbnail: Optional[str]
    duration: Optional[float]
    views: Optional[int]
    published_at: Optional[int]
    username: Optional[str]
    author_avatar: Optional[str]
    author_verified: Optional[bool]
    likes: Optional[int]
    comments: Optional[int]
    shares: Optional[int]
    saves: Optional[int]
    location: Optional[str]
    region: Optional[str]
    music: Optional[dict]


class DownloadResult(TypedDict):
    """``/v1/download`` and ``/v1/{platform}``."""

    success: Literal[True]
    platform: str
    type: str
    source_url: str
    video_id: Optional[str]
    medias: list[Media]
    music: Optional[Media]
    meta: Meta
    formats: NotRequired[list[Format]]
    recommended_format: NotRequired[Optional[str]]
    credits: Credits


class YouTubeFormat(TypedDict):
    quality: str
    file_size: Optional[int]
    file_size_str: Optional[str]
    exact: bool


class YouTubeInfo(TypedDict):
    success: Literal[True]
    platform: Literal["youtube"]
    source_url: str
    video_id: str
    title: str
    author: Optional[str]
    duration_seconds: Optional[int]
    duration_str: Optional[str]
    thumbnail: Optional[str]
    is_short: bool
    formats: list[YouTubeFormat]
    audio_formats: list[YouTubeFormat]
    credits: Credits


class YouTubeLink(TypedDict):
    success: Literal[True]
    platform: Literal["youtube"]
    source_url: str
    video_id: str
    url: str
    filename: str
    quality: str
    mode: Literal["video", "audio"]
    ext: str
    file_size: Optional[int]
    file_size_str: Optional[str]
    exact: bool
    seekable: bool
    expires: int
    title: str
    duration_seconds: Optional[int]
    duration_str: Optional[str]
    thumbnail: Optional[str]
    credits: Credits


class Detection(TypedDict):
    success: Literal[True]
    supported: bool
    platform: Optional[str]
    name: NotRequired[Optional[str]]
    host: NotRequired[Optional[str]]
    formats: NotRequired[bool]


YouTubeQuality = Literal["144p", "240p", "360p", "480p", "720p", "1080p", "mp3", "m4a"]
