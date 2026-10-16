import uvicorn
from fastapi import FastAPI
from pydantic import ValidationError

from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.service_items import router as service_items_router
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.rate_limit import SlidingWindowLimiter
from app.core.responses import UTF8JSONResponse


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    application = FastAPI(
        title="campus-service-assistant",
        default_response_class=UTF8JSONResponse,
    )
    application.state.settings = resolved
    # 限流器随应用实例创建：测试可为每个实例单独设定阈值，互不影响
    application.state.chat_limiter = SlidingWindowLimiter(
        max_requests=resolved.chat_rate_limit_requests,
        window_seconds=resolved.chat_rate_limit_window_seconds,
    )
    application.include_router(health_router)
    application.include_router(service_items_router)
    application.include_router(chat_router)
    application.include_router(conversations_router)
    application.include_router(feedback_router)
    application.include_router(knowledge_router)
    register_error_handlers(application)
    return application


try:
    app = create_app()
except ValidationError as exc:
    issue = exc.errors()[0]
    print(f"配置校验失败：{issue['loc'][0]}（{issue['msg']}），请检查环境变量或 .env 文件后重试")
    raise SystemExit(1) from None


def main() -> None:
    settings = app.state.settings
    uvicorn.run(app, host="0.0.0.0", port=settings.app_port)


if __name__ == "__main__":
    main()