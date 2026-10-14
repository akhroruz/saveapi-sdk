"""Python client for saveapi.org — one REST API to download media from
Instagram, TikTok, YouTube, Facebook, X, Pinterest, Likee, Snapchat,
Threads, VK, Rutube, 9GAG and Twitch.

Docs: https://saveapi.org/en/docs/
"""

from ._client import AsyncSaveAPI, SaveAPI, __version__
from .errors import RETRYABLE_CODES, SaveAPIError

__all__ = ["SaveAPI", "AsyncSaveAPI", "SaveAPIError", "RETRYABLE_CODES", "__version__"]
