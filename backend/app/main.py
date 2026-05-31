import asyncio
import logging
import os
import socket
import sys
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from backend.app.database import SessionLocal, Base, engine
from backend.app.logging_config import setup_logging
from backend.app.exceptions import register_exception_handlers
from backend.app.models.user import User
from backend.app.models.record import UserStats
from backend.app.services.auth_service import hash_password
from backend.app.services.achievement_service import ensure_default_achievements
from backend.app.routers import (
    auth_router, units_router, questions_router, records_router,
    scores_router, achievements_router, leaderboard_router, admin_router, pvp_router,
)
from backend.app.ws.router import online_websocket_endpoint
from backend.app.ws.manager import manager

logger = logging.getLogger(__name__)

_should_open_browser = False
_browser_url = "http://localhost"


def _get_local_ip() -> tuple[str, bool]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0], True
    except Exception:
        return "127.0.0.1", False


async def _delayed_browser_open(url: str):
    await asyncio.sleep(1.5)
    webbrowser.open(url)


def _seed_default_admin() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == "admin").first()
        if existing:
            return
        admin = User(
            username="admin",
            original_username="admin",
            password_hash=hash_password("admin123"),
            nickname="管理员",
            role="admin",
            force_password_change=True,
        )
        db.add(admin)
        db.flush()
        stats = UserStats(user_id=admin.id)
        db.add(stats)
        db.commit()
        logger.info("已创建默认管理员账号 admin / admin123，首次登录需修改密码")
    finally:
        db.close()


def _seed_default_achievements() -> None:
    db = SessionLocal()
    try:
        ensure_default_achievements(db)
        db.commit()
    finally:
        db.close()


def _ensure_schema() -> None:
    # Import the model registry before create_all so packaged first-run can self-bootstrap.
    import backend.app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def _get_frontend_dist() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / "frontend" / "dist"
    return Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def _spa_index_response(frontend_dist: Path) -> FileResponse:
    return FileResponse(
        frontend_dist / "index.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_schema()
    _seed_default_admin()
    _seed_default_achievements()
    manager.bind_loop(asyncio.get_running_loop())
    cleanup_task = asyncio.create_task(manager.check_stale_connections())
    if _should_open_browser:
        asyncio.create_task(_delayed_browser_open(_browser_url))
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


def create_app(dev_mode: bool = False) -> FastAPI:
    setup_logging(dev_mode=dev_mode)
    app = FastAPI(title="Integrated-Education-Platform API", version="2.2.12", lifespan=lifespan)
    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_credentials=False,
        allow_methods=["*"], allow_headers=["*"],
    )
    # Dual prefix: /api/v1/ + legacy /api/ (include_in_schema=False for old)
    for router in [auth_router, units_router, questions_router, records_router,
                   scores_router, achievements_router, leaderboard_router, admin_router, pvp_router]:
        app.include_router(router, prefix="/api/v1")
        app.include_router(router, prefix="/api", include_in_schema=False)
    app.add_api_websocket_route("/ws/online", online_websocket_endpoint)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    frontend_dist = _get_frontend_dist()
    if frontend_dist.exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/app/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/app", include_in_schema=False)
        @app.get("/app/", include_in_schema=False)
        @app.get("/app/{rest:path}", include_in_schema=False)
        async def serve_spa(rest: str = ""):
            if rest:
                file_path = frontend_dist / rest
                if file_path.is_file():
                    return FileResponse(file_path)
            return _spa_index_response(frontend_dist)

    @app.get("/admin", include_in_schema=False)
    @app.get("/admin/", include_in_schema=False)
    @app.get("/admin/{rest:path}", include_in_schema=False)
    def admin_redirect(rest: str = ""):
        return RedirectResponse(url="/app/admin")

    @app.get("/")
    def root():
        return RedirectResponse(url="/app/")

    return app


app = create_app(dev_mode=os.environ.get("GAME_DEV_MODE", "").lower() in ("1", "true", "yes"))


def run_server(host="0.0.0.0", port=None):
    import uvicorn
    if port is None:
        port = int(os.environ.get("GAME_PORT", "80"))

    local_ip, ip_ok = _get_local_ip()

    def _url(h: str, p: int) -> str:
        return f"http://{h}" + (f":{p}" if p != 80 else "")

    def _print_banner(p: int):
        print("=" * 40)
        print("  Integrated-Education-Platform Server v2.2.12")
        print(f"  首页:     {_url('localhost', p)}/")
        print(f"  管理端:   {_url('localhost', p)}/app/admin")
        if ip_ok:
            print(f"  局域网:   {_url(local_ip, p)}/")
        print("=" * 40)

    global _should_open_browser, _browser_url
    _should_open_browser = True
    _browser_url = _url("localhost", port) + "/app/admin"
    _print_banner(port)
    import sys as _sys
    _sys.stdout.flush()

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--dev", action="store_true")
    args = parser.parse_args()
    if args.dev:
        os.environ["GAME_DEV_MODE"] = "true"
    run_server(port=args.port)
