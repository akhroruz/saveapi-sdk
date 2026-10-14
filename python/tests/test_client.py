import httpx
import pytest

from saveapi import AsyncSaveAPI, SaveAPI, SaveAPIError
from saveapi import _client

OK = {
    "success": True, "platform": "tiktok", "type": "video",
    "source_url": "https://www.tiktok.com/@a/video/1", "video_id": "1",
    "medias": [{"type": "video", "url": "https://cdn/x.mp4", "ext": "mp4", "quality": None,
                "width": 0, "height": 0, "size_mb": 1.0, "watermark": False}],
    "music": None, "meta": {}, "credits": {"spent": 1.5, "remaining": 998.5},
}


def _error(status, code, headers=None):
    return httpx.Response(status, json={"success": False, "error": {"code": code, "message": code.lower()}},
                          headers=headers or {})


def _client_with(handler, **kwargs):
    return SaveAPI("sk_test", http_client=httpx.Client(transport=httpx.MockTransport(handler)), **kwargs)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    slept = []
    monkeypatch.setattr(_client.time, "sleep", slept.append)

    async def fake_async_sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr(_client.asyncio, "sleep", fake_async_sleep)
    return slept


def test_download_sends_bearer_key_and_url():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["Authorization"]
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        seen["ua"] = request.headers["User-Agent"]
        return httpx.Response(200, json=OK)

    result = _client_with(handler).download("https://www.tiktok.com/@a/video/1", full_meta=True)

    assert result["medias"][0]["url"] == "https://cdn/x.mp4"
    assert seen["auth"] == "Bearer sk_test"
    assert seen["path"] == "/v1/download"
    assert seen["params"] == {"url": "https://www.tiktok.com/@a/video/1", "full_meta": "true"}
    assert seen["ua"].startswith("saveapi-python/")


def test_false_flags_and_none_are_not_sent():
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=OK)

    _client_with(handler).platform("tiktok", "https://t/1")
    assert seen["params"] == {"url": "https://t/1"}


def test_final_error_is_raised_without_retry(no_sleep):
    calls = []

    def handler(request):
        calls.append(1)
        return _error(403, "PRIVATE_CONTENT")

    with pytest.raises(SaveAPIError) as exc:
        _client_with(handler, max_retries=3).download("https://t/1")

    assert exc.value.code == "PRIVATE_CONTENT"
    assert exc.value.status == 403
    assert exc.value.retryable is False
    assert len(calls) == 1
    assert no_sleep == []


def test_upstream_timeout_is_retried_once_by_default(no_sleep):
    answers = iter([_error(504, "UPSTREAM_TIMEOUT"), httpx.Response(200, json=OK)])
    result = _client_with(lambda request: next(answers)).download("https://t/1")
    assert result["success"] is True
    assert no_sleep == [1.0]


def test_retries_are_bounded():
    calls = []

    def handler(request):
        calls.append(1)
        return _error(502, "UPSTREAM_ERROR")

    with pytest.raises(SaveAPIError):
        _client_with(handler, max_retries=2).download("https://t/1")
    assert len(calls) == 3


def test_rate_limit_waits_for_retry_after(no_sleep):
    answers = iter([_error(429, "RATE_LIMITED", {"Retry-After": "7"}), httpx.Response(200, json=OK)])
    _client_with(lambda request: next(answers)).download("https://t/1")
    assert no_sleep == [7.0]


def test_quota_exceeded_is_final():
    with pytest.raises(SaveAPIError) as exc:
        _client_with(lambda request: _error(429, "QUOTA_EXCEEDED")).download("https://t/1")
    assert exc.value.code == "QUOTA_EXCEEDED"
    assert exc.value.retryable is False


def test_key_from_environment(monkeypatch):
    monkeypatch.setenv("SAVEAPI_KEY", "sk_env")
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["Authorization"]
        return httpx.Response(200, json={"success": True, "supported": True, "platform": "tiktok"})

    SaveAPI(http_client=httpx.Client(transport=httpx.MockTransport(handler))).detect("https://t/1")
    assert seen["auth"] == "Bearer sk_env"


def test_missing_key_explains_where_to_get_one(monkeypatch):
    monkeypatch.delenv("SAVEAPI_KEY", raising=False)
    with pytest.raises(ValueError, match="saveapi.org"):
        SaveAPI()


def test_youtube_create_passes_quality():
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"success": True, "url": "https://api.saveapi.org/tunnel?id=1"})

    _client_with(handler).youtube_create("https://youtu.be/x", "mp3")
    assert seen["params"] == {"url": "https://youtu.be/x", "quality": "mp3"}


def test_instagram_profile_needs_username_or_url():
    with pytest.raises(ValueError):
        _client_with(lambda request: httpx.Response(200, json={})).instagram_profile()


def test_non_json_error_still_raises():
    with pytest.raises(SaveAPIError) as exc:
        _client_with(lambda request: httpx.Response(502, text="<html>bad gateway</html>")).me()
    assert exc.value.status == 502
    assert exc.value.code == "HTTP_ERROR"


async def test_async_client_retries_and_returns(no_sleep):
    answers = iter([_error(504, "UPSTREAM_TIMEOUT"), httpx.Response(200, json=OK)])
    transport = httpx.MockTransport(lambda request: next(answers))
    async with AsyncSaveAPI("sk_test", http_client=httpx.AsyncClient(transport=transport)) as api:
        result = await api.download("https://t/1")
    assert result["platform"] == "tiktok"
    assert no_sleep == [1.0]
