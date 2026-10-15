from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

ERROR_MAP: dict[int, tuple[str, str]] = {
    status.HTTP_404_NOT_FOUND: ("INVALID_REQUEST", "资源不存在"),
    status.HTTP_405_METHOD_NOT_ALLOWED: ("INVALID_REQUEST", "请求方法不支持"),
    status.HTTP_422_UNPROCESSABLE_CONTENT: ("INVALID_REQUEST", "请求参数校验失败"),
    status.HTTP_500_INTERNAL_SERVER_ERROR: ("INTERNAL_ERROR", "服务内部错误，请稍后重试"),
}


class BusinessError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def error_response(status_code: int) -> JSONResponse:
    code, message = ERROR_MAP.get(
        status_code, ERROR_MAP[status.HTTP_500_INTERNAL_SERVER_ERROR]
    )
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        media_type="application/json; charset=utf-8",
    )


def business_error_response(exc: BusinessError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
        media_type="application/json; charset=utf-8",
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        return error_response(exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError):
        return error_response(status.HTTP_422_UNPROCESSABLE_CONTENT)

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception):
        return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(BusinessError)
    async def handle_business_exception(request: Request, exc: BusinessError):
        return business_error_response(exc)
