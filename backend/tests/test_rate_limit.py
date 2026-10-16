from fastapi.testclient import TestClient
from starlette.requests import Request as StarletteRequest

from app.core.rate_limit import SlidingWindowLimiter, rate_limit_key
from app.services.llm_client import MockLLMClient, get_llm_client


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _request(host: str = "1.2.3.4") -> StarletteRequest:
    return StarletteRequest({"type": "http", "client": (host, 1234), "headers": []})


def test_allows_up_to_limit_then_rejects():
    limiter = SlidingWindowLimiter(
        max_requests=3, window_seconds=60, clock=_FakeClock()
    )
    assert [limiter.allow("k") for _ in range(4)] == [True, True, True, False]


def test_window_slides_and_frees_quota():
    clock = _FakeClock()
    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert limiter.allow("k") is True
    assert limiter.allow("k") is True
    assert limiter.allow("k") is False
    clock.advance(61)
    assert limiter.allow("k") is True


def test_rejected_request_is_not_counted():
    clock = _FakeClock()
    limiter = SlidingWindowLimiter(max_requests=1, window_seconds=60, clock=clock)
    assert limiter.allow("k") is True
    assert limiter.allow("k") is False
    clock.advance(61)
    # 只有 1 次被计入窗口，因此窗口滑过后立即恢复额度
    assert limiter.allow("k") is True


def test_keys_are_isolated():
    limiter = SlidingWindowLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("a") is True
    assert limiter.allow("b") is True
    assert limiter.allow("a") is False


def test_reset_clears_state():
    limiter = SlidingWindowLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("k") is True
    limiter.reset()
    assert limiter.allow("k") is True


def test_invalid_config_is_clamped():
    limiter = SlidingWindowLimiter(max_requests=0, window_seconds=0)
    assert limiter.max_requests == 1
    assert limiter.window_seconds == 1.0


def test_rate_limit_key_prefers_session_token():
    assert rate_limit_key(_request(), "abc") == "token:abc"
    assert rate_limit_key(_request(), "  abc  ") == "token:abc"


def test_rate_limit_key_falls_back_to_host():
    assert rate_limit_key(_request("9.9.9.9"), None) == "host:9.9.9.9"
    assert rate_limit_key(_request("9.9.9.9"), "   ") == "host:9.9.9.9"


def test_rate_limit_key_without_client():
    request = StarletteRequest({"type": "http", "headers": []})
    assert rate_limit_key(request, None) == "host:unknown"


def _post(db_client: TestClient, token: str):
    return db_client.post(
        "/api/chat/messages",
        json={"conversation_id": None, "message": "食堂几点开门？"},
        headers={"X-Session-Token": token},
    )


def _stub_llm(db_client: TestClient) -> None:
    # 本文件测的是限流，不是模型：「食堂几点开门？」会先走 smalltalk 分类
    # （真实模型调用会触网且不稳定），注入确定性替身隔离该依赖
    db_client.app.dependency_overrides[get_llm_client] = lambda: MockLLMClient()


def test_endpoint_returns_429_after_limit(db_client: TestClient):
    db_client.app.state.chat_limiter = SlidingWindowLimiter(
        max_requests=2, window_seconds=60
    )
    _stub_llm(db_client)
    for _ in range(2):
        assert _post(db_client, "rl-token").status_code == 200

    limited = _post(db_client, "rl-token")
    assert limited.status_code == 429
    assert limited.json() == {
        "error": {"code": "RATE_LIMITED", "message": "请求过于频繁，请稍后重试"}
    }


def test_endpoint_limit_is_per_identity(db_client: TestClient):
    db_client.app.state.chat_limiter = SlidingWindowLimiter(
        max_requests=1, window_seconds=60
    )
    _stub_llm(db_client)
    assert _post(db_client, "token-a").status_code == 200
    assert _post(db_client, "token-a").status_code == 429
    # 另一个标识不受影响
    assert _post(db_client, "token-b").status_code == 200
