"""AgentArts 工作流客户端测试：mock httpx 传输层，不产生真实网络请求。

覆盖：请求组装、常见输出结构解析、超时/连接异常的重试与错误映射、
429 与 4xx 不重试、配置缺失、get_llm_client 路由优先级。
"""

import httpx
import pytest

from app.services import agentarts_client
from app.services.agentarts_client import AgentArtsClient
from app.services.llm_client import (
    LLMClient,
    LLMTimeoutError,
    LLMUpstreamError,
    MaaSClient,
    MockLLMClient,
    UnavailableLLMClient,
    get_llm_client,
)


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload=None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("响应不是合法 JSON")
        return self._payload


class _FakeHTTPClient:
    """替换 httpx.Client：记录请求与调用次数，回放预置响应或异常。"""

    calls = 0
    last_request: dict = {}
    response = _FakeResponse()
    error: Exception | None = None

    def __init__(self, timeout=None) -> None:
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> bool:
        return False

    def post(self, url, json=None, headers=None):
        type(self).calls += 1
        type(self).last_request = {"url": url, "json": json, "headers": headers}
        if type(self).error is not None:
            raise type(self).error
        return type(self).response


@pytest.fixture
def fake_http(monkeypatch):
    _FakeHTTPClient.calls = 0
    _FakeHTTPClient.error = None
    _FakeHTTPClient.response = _FakeResponse(200, {"output": {"text": '{"status":"answered"}'}})
    monkeypatch.setattr(agentarts_client.httpx, "Client", _FakeHTTPClient)
    return _FakeHTTPClient


def _client(**overrides) -> AgentArtsClient:
    params = {
        "api_key": "secret",
        "agent_id": "agent-001",
        "base_url": "https://agentarts.example.com/v1/run",
    }
    params.update(overrides)
    return AgentArtsClient(**params)


def test_agentarts_client_builds_workflow_request(fake_http):
    content = _client().complete("SYS", "USER")
    assert content == '{"status":"answered"}'
    request = fake_http.last_request
    assert request["url"] == "https://agentarts.example.com/v1/run"
    assert request["headers"]["Authorization"] == "Bearer secret"
    assert request["json"]["agent_id"] == "agent-001"
    assert request["json"]["inputs"] == {"question": "USER", "system_prompt": "SYS"}
    assert request["json"]["stream"] is False
    assert fake_http.calls == 1


def test_agentarts_client_strips_trailing_slash_in_base_url(fake_http):
    _client(base_url="https://agentarts.example.com/v1/run/").complete("s", "u")
    assert fake_http.last_request["url"] == "https://agentarts.example.com/v1/run"


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"output": {"text": "A"}}, "A"),
        ({"data": {"output": {"text": "B"}}}, "B"),
        ({"data": {"output": "C"}}, "C"),
        ({"output": "D"}, "D"),
        ({"answer": "E"}, "E"),
        ({"content": "F"}, "F"),
        ({"choices": [{"message": {"content": "G"}}]}, "G"),
    ],
)
def test_agentarts_client_parses_common_output_shapes(fake_http, payload, expected):
    fake_http.response = _FakeResponse(200, payload)
    assert _client().complete("s", "u") == expected


def test_agentarts_client_timeout_retries_then_maps_to_timeout_error(fake_http):
    fake_http.error = httpx.ReadTimeout("slow")
    with pytest.raises(LLMTimeoutError):
        _client().complete("s", "u")
    assert fake_http.calls == 2  # 缺省 max_attempts=2


def test_agentarts_client_connect_error_maps_to_upstream_error(fake_http):
    fake_http.error = httpx.ConnectError("boom")
    with pytest.raises(LLMUpstreamError):
        _client().complete("s", "u")


def test_agentarts_client_respects_max_attempts(fake_http):
    fake_http.error = httpx.ConnectError("boom")
    with pytest.raises(LLMUpstreamError):
        _client(max_attempts=3).complete("s", "u")
    assert fake_http.calls == 3


def test_agentarts_client_rate_limit_not_retried(fake_http):
    fake_http.response = _FakeResponse(429, {"error": "rate limited"})
    with pytest.raises(LLMUpstreamError) as excinfo:
        _client().complete("s", "u")
    assert excinfo.value.status_code == 429
    assert fake_http.calls == 1


def test_agentarts_client_http_error_keeps_status_code(fake_http):
    fake_http.response = _FakeResponse(401, {"error": "unauthorized"})
    with pytest.raises(LLMUpstreamError) as excinfo:
        _client().complete("s", "u")
    assert excinfo.value.status_code == 401
    assert fake_http.calls == 1


def test_agentarts_client_malformed_body_maps_to_upstream_error(fake_http):
    fake_http.response = _FakeResponse(200, None)
    with pytest.raises(LLMUpstreamError):
        _client().complete("s", "u")


def test_agentarts_client_unknown_output_shape_maps_to_upstream_error(fake_http):
    fake_http.response = _FakeResponse(200, {"unexpected": True})
    with pytest.raises(LLMUpstreamError):
        _client().complete("s", "u")


def test_agentarts_client_empty_output_maps_to_upstream_error(fake_http):
    fake_http.response = _FakeResponse(200, {"output": {"text": "  "}})
    with pytest.raises(LLMUpstreamError):
        _client().complete("s", "u")


def test_agentarts_client_without_api_key_rejects_call():
    with pytest.raises(LLMUpstreamError):
        _client(api_key="").complete("s", "u")


def test_agentarts_client_without_agent_id_rejects_call():
    with pytest.raises(LLMUpstreamError):
        _client(agent_id="").complete("s", "u")


def test_agentarts_client_without_base_url_rejects_call():
    with pytest.raises(LLMUpstreamError):
        _client(base_url="").complete("s", "u")


def test_get_llm_client_prefers_agentarts_when_configured(monkeypatch):
    monkeypatch.setenv("AGENTARTS_API_KEY", "agent-key")
    monkeypatch.setenv("AGENTARTS_AGENT_ID", "agent-001")
    monkeypatch.setenv("MAAS_API_KEY", "maas-key")
    assert isinstance(get_llm_client(), AgentArtsClient)


def test_get_llm_client_falls_back_to_maas_without_agent_id(monkeypatch):
    """只配了 api_key 没配 agent_id 时不应路由到 AgentArts（调用必然失败）。"""
    monkeypatch.setenv("AGENTARTS_API_KEY", "agent-key")
    monkeypatch.setenv("AGENTARTS_AGENT_ID", "")
    monkeypatch.setenv("MAAS_API_KEY", "maas-key")
    assert isinstance(get_llm_client(), MaaSClient)


def test_get_llm_client_uses_mock_in_local_env_without_key(monkeypatch):
    monkeypatch.setenv("AGENTARTS_API_KEY", "")
    monkeypatch.setenv("AGENTARTS_AGENT_ID", "")
    monkeypatch.setenv("MAAS_API_KEY", "")
    monkeypatch.setenv("APP_ENV", "local")
    assert isinstance(get_llm_client(), MockLLMClient)


def test_get_llm_client_never_falls_back_to_mock_in_production(monkeypatch):
    monkeypatch.setenv("AGENTARTS_API_KEY", "")
    monkeypatch.setenv("AGENTARTS_AGENT_ID", "")
    monkeypatch.setenv("MAAS_API_KEY", "")
    monkeypatch.setenv("APP_ENV", "production")
    client = get_llm_client()
    assert isinstance(client, UnavailableLLMClient)
    with pytest.raises(LLMUpstreamError):
        client.complete("s", "u")


def test_agentarts_client_satisfies_protocol():
    assert isinstance(_client(), LLMClient)
