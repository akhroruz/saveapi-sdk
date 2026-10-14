"""Errors raised by the client.

Every failed call raises :class:`SaveAPIError`. Match on ``error.code`` —
the codes are stable, the messages are not.
"""

from __future__ import annotations

#: Codes a retry can fix. Everything else is a final answer: retrying a
#: private or deleted post does not change it, and where the error is billed
#: (0.1 credit for a link the source refuses) it costs another credit.
RETRYABLE_CODES = frozenset({"UPSTREAM_TIMEOUT", "UPSTREAM_ERROR", "RATE_LIMITED"})


class SaveAPIError(Exception):
    """A non-2xx answer from api.saveapi.org.

    Attributes:
        code: Stable error code, e.g. ``PRIVATE_CONTENT`` or ``QUOTA_EXCEEDED``.
            Full list: https://saveapi.org/en/docs/#errors
        message: Human-readable explanation (may change between releases).
        status: HTTP status code.
        retry_after: Seconds to wait, set on ``RATE_LIMITED``.
    """

    def __init__(self, code: str, message: str, status: int, retry_after: float | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status
        self.retry_after = retry_after

    @property
    def retryable(self) -> bool:
        """True when sending the same request again can succeed."""
        return self.code in RETRYABLE_CODES
