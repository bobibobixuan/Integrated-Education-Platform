class AppError(Exception):
    """Base business exception"""
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


class AuthError(AppError):
    def __init__(self, detail: str = "认证失败"):
        super().__init__(detail, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, detail: str = "无权限"):
        super().__init__(detail, status_code=403)


class NotFoundError(AppError):
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(detail, status_code=404)


class ConflictError(AppError):
    def __init__(self, detail: str = "资源冲突"):
        super().__init__(detail, status_code=409)


class RoomFullError(ConflictError):
    def __init__(self, detail: str = "房间已满"):
        super().__init__(detail)


class BattleExpiredError(ConflictError):
    def __init__(self, detail: str = "对战已过期"):
        super().__init__(detail)


from fastapi import Request
from fastapi.responses import JSONResponse


def register_exception_handlers(app):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        import structlog
        logger = structlog.get_logger()
        logger.error("unhandled_error", path=str(request.url), error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})
