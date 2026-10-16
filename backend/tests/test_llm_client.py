import json

import httpx
import pytest

from app.services import llm_client
from app.services.llm_client import (
    LLMClient,
    LLMTimeoutError,
    LLMUpstreamError,
    MOCK_STANDIN_NOTICE,
    MaaSClient,
    MockLLMClient,
    UnavailableLLMClient,
    get_llm_client,
)


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("响应不是合法 JSON")
        return self._payload


class _FakeHTTPClient:
    """替换 httpx.Client：只记录请求并回放预置响应，不产生真实网络请求。"""

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
        type(self).last_request = {"url": url, "json": json, "headers": headers}
        if type(self).error is not None:
            raise type(self).error
        return type(self).response


@pytest.fixture
def fake_http(monkeypatch):
    _FakeHTTPClient.last_request = {}
    _FakeHTTPClient.error = None
    _FakeHTTPClient.response = _FakeResponse(
        200, {"choices": [{"message": {"content": "ok"}}]}
    )
    monkeypatch.setattr(llm_client.httpx, "Client", _FakeHTTPClient)
    return _FakeHTTPClient


def _client(**overrides) -> MaaSClient:
    params = {
        "api_key": "secret",
        "base_url": "https://api.modelarts-maas.com/v2",
        "model": "DeepSeek-V3",
    }
    params.update(overrides)
    return MaaSClient(**params)


def test_maas_client_builds_openai_compatible_request(fake_http):
    content = _client().complete("SYS", "USER")
    assert content == "ok"
    request = fake_http.last_request
    assert request["url"] == "https://api.modelarts-maas.com/v2/chat/completions"
    assert request["headers"]["Authorization"] == "Bearer secret"
    assert request["json"]["model"] == "DeepSeek-V3"
    assert request["json"]["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USER"},
    ]
    assert request["json"]["stream"] is False


def test_maas_client_strips_trailing_slash_in_base_url(fake_http):
    _client(base_url="https://api.modelarts-maas.com/v2/").complete("s", "u")
    assert fake_http.last_request["url"].endswith("/v2/chat/completions")


def test_maas_client_accepts_full_endpoint_in_base_url(fake_http):
    """控制台给出的地址可能已含 /chat/completions，不能重复拼接（否则 404）。"""
    _client(base_url="https://api.modelarts-maas.com/v2/chat/completions").complete("s", "u")
    assert fake_http.last_request["url"] == "https://api.modelarts-maas.com/v2/chat/completions"


def test_maas_client_disables_thinking_by_default(fake_http):
    """推理模型默认产出思考链，会挤占 max_tokens 并显著拉长耗时，因此默认关闭。"""
    _client().complete("s", "u")
    assert fake_http.last_request["json"]["thinking"] == {"type": "disabled"}


def test_maas_client_can_keep_thinking_enabled(fake_http):
    _client(disable_thinking=False).complete("s", "u")
    assert "thinking" not in fake_http.last_request["json"]


def test_maas_client_timeout_maps_to_timeout_error(fake_http):
    fake_http.error = httpx.ReadTimeout("slow")
    with pytest.raises(LLMTimeoutError):
        _client().complete("s", "u")


def test_maas_client_connect_error_maps_to_upstream_error(fake_http):
    fake_http.error = httpx.ConnectError("boom")
    with pytest.raises(LLMUpstreamError):
        _client().complete("s", "u")


def test_maas_client_http_error_keeps_status_code(fake_http):
    fake_http.response = _FakeResponse(
        401, {"error": "unauthorized"}, text='{"error":{"code":"ModelArts.81001"}}'
    )
    with pytest.raises(LLMUpstreamError) as excinfo:
        _client().complete("s", "u")
    assert excinfo.value.status_code == 401


def test_maas_client_malformed_body_maps_to_upstream_error(fake_http):
    fake_http.response = _FakeResponse(200, {"unexpected": True})
    with pytest.raises(LLMUpstreamError):
        _client().complete("s", "u")


def test_maas_client_empty_content_maps_to_upstream_error(fake_http):
    fake_http.response = _FakeResponse(200, {"choices": [{"message": {"content": "  "}}]})
    with pytest.raises(LLMUpstreamError):
        _client().complete("s", "u")


def test_maas_client_without_api_key_rejects_call():
    with pytest.raises(LLMUpstreamError):
        _client(api_key="").complete("s", "u")


def test_get_llm_client_uses_maas_when_key_present(monkeypatch):
    monkeypatch.setenv("MAAS_API_KEY", "secret-key")
    assert isinstance(get_llm_client(), MaaSClient)


def test_get_llm_client_uses_mock_in_local_env_without_key(monkeypatch):
    monkeypatch.setenv("MAAS_API_KEY", "")
    monkeypatch.setenv("APP_ENV", "local")
    assert isinstance(get_llm_client(), MockLLMClient)


def test_get_llm_client_never_falls_back_to_mock_in_production(monkeypatch):
    """生产环境缺密钥时必须明确失败，不能静默用替身给出假答案。"""
    monkeypatch.setenv("MAAS_API_KEY", "")
    monkeypatch.setenv("APP_ENV", "production")
    client = get_llm_client()
    assert isinstance(client, UnavailableLLMClient)
    with pytest.raises(LLMUpstreamError):
        client.complete("s", "u")


def test_mock_client_default_is_labeled_placeholder():
    """缺省输出必须显式标注为替身结果，且事项名取自提示词，不张冠李戴。"""
    payload = json.loads(
        MockLLMClient().complete("s", "【事项】转专业咨询\n【学生问题】转专业需要什么条件？")
    )
    assert payload["title"] == "转专业咨询"
    assert MOCK_STANDIN_NOTICE in payload["summary"]
    assert MOCK_STANDIN_NOTICE in payload["warnings"]
    assert payload["steps"] == []


def test_mock_client_placeholder_without_item_line():
    payload = json.loads(MockLLMClient().complete("s", "没有任何结构化提示"))
    assert payload["title"] == "校园办事咨询"


def test_mock_client_routes_by_keyword():
    client = MockLLMClient(responses={"请假": '{"status": "insufficient_evidence"}'})
    assert client.complete("s", "我想请假") == '{"status": "insufficient_evidence"}'
    assert MOCK_STANDIN_NOTICE in client.complete("s", "【事项】学生证补办")


def test_mock_client_can_raise_configured_error():
    client = MockLLMClient(error=LLMTimeoutError("慢"))
    with pytest.raises(LLMTimeoutError):
        client.complete("s", "u")


def test_all_implementations_satisfy_protocol():
    assert isinstance(MockLLMClient(), LLMClient)
    assert isinstance(UnavailableLLMClient(), LLMClient)
    assert isinstance(_client(), LLMClient)
