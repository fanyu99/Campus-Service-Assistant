"""问答接口的进程内滑动窗口限流（契约 §6.7、OWASP A04）。

原型期为单实例部署，不引入 Redis：多 worker 或多副本时各自计数（实际阈值 = 配置值 × 副本数），
已在部署说明中注明；如需严格全局限流，可把 ``SlidingWindowLimiter`` 换成 Redis 计数实现，
调用方（依赖注入与端点）无需改动。
"""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable

from fastapi import Request

# 键数量上限：超过后清理空桶，避免长期运行内存无界增长
_MAX_KEYS = 10_000


class SlidingWindowLimiter:
    """按 key（匿名会话标识 / 客户端地址）统计窗口内的请求次数。"""

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_requests = max(1, max_requests)
        self._window_seconds = max(1.0, window_seconds)
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    @property
    def max_requests(self) -> int:
        return self._max_requests

    @property
    def window_seconds(self) -> float:
        return self._window_seconds

    def allow(self, key: str) -> bool:
        """记录一次请求；超限返回 False（该次请求不计入窗口）。"""
        now = self._clock()
        cutoff = now - self._window_seconds
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self._max_requests:
                return False
            hits.append(now)
            if len(self._hits) > _MAX_KEYS:
                for stale_key in [k for k, v in self._hits.items() if not v]:
                    del self._hits[stale_key]
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def get_chat_limiter(request: Request) -> SlidingWindowLimiter:
    """依赖注入入口：限流器随应用实例创建（测试可为每个 app 实例单独设定阈值）。"""
    return request.app.state.chat_limiter


def rate_limit_key(request: Request, session_token: str | None) -> str:
    """优先按匿名会话标识计数；缺失时退化为客户端地址。"""
    if session_token and session_token.strip():
        return f"token:{session_token.strip()[:64]}"
    client = request.client
    return f"host:{client.host}" if client is not None else "host:unknown"
