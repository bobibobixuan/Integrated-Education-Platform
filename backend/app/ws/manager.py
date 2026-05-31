import asyncio
import time
from fastapi import WebSocket
from backend.app.database import SessionLocal
from backend.app.ws.auth_cache import AuthCache
from backend.app.models.user import User


class ConnectionManager:
    def __init__(self):
        self.student_connections: dict[int, list[tuple[WebSocket, float]]] = {}
        self.admin_connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self.auth_cache = AuthCache()
        self._throttle_pending: dict[tuple[str, str], tuple[dict, asyncio.Task | None]] = {}

    def bind_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def schedule(self, coro) -> None:
        if self._loop is None or self._loop.is_closed():
            coro.close()
            return
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None
        async def _safe():
            try:
                await coro
            except Exception:
                import traceback
                traceback.print_exc()
        if running_loop is self._loop:
            asyncio.create_task(_safe())
        else:
            asyncio.run_coroutine_threadsafe(_safe(), self._loop)

    async def connect_student(self, ws: WebSocket, user_id: int):
        async with self._lock:
            if user_id not in self.student_connections:
                self.student_connections[user_id] = []
            self.student_connections[user_id].append((ws, time.time()))
        await self._broadcast_status()
        from backend.app.services.pvp_service import schedule_pvp_student_refresh_for_user
        schedule_pvp_student_refresh_for_user(user_id)

    async def heartbeat(self, user_id: int):
        async with self._lock:
            if user_id in self.student_connections:
                conns = self.student_connections[user_id]
                now = time.time()
                self.student_connections[user_id] = [(ws, now) for ws, _ in conns]

    async def disconnect_student(self, ws: WebSocket, user_id: int):
        async with self._lock:
            if user_id in self.student_connections:
                self.student_connections[user_id] = [
                    (w, h) for w, h in self.student_connections[user_id] if w != ws
                ]
                if not self.student_connections[user_id]:
                    del self.student_connections[user_id]
        await self._broadcast_status()

    async def connect_admin(self, ws: WebSocket):
        async with self._lock:
            self.admin_connections.add(ws)
        await self._broadcast_status()

    async def disconnect_admin(self, ws: WebSocket):
        async with self._lock:
            self.admin_connections.discard(ws)

    async def send_to_admins(self, payload: dict) -> None:
        async with self._lock:
            admins = list(self.admin_connections)
        dead = set()
        for ws in admins:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.add(ws)
        if dead:
            async with self._lock:
                for d in dead:
                    self.admin_connections.discard(d)

    async def send_to_student(self, user_id: int, payload: dict) -> None:
        async with self._lock:
            conns = list(self.student_connections.get(user_id, []))
        if not conns:
            return
        dead = []
        for ws, _ in conns:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                conns = self.student_connections.get(user_id, [])
                conns = [(ws, h) for ws, h in conns if ws not in dead]
                if conns:
                    self.student_connections[user_id] = conns
                else:
                    self.student_connections.pop(user_id, None)

    def send_throttled(self, user_id: int | None, payload: dict, throttle_key: str = "") -> None:
        msg_type = payload.get("type", "")
        key = (msg_type, throttle_key or str(user_id))
        existing = self._throttle_pending.get(key)
        if existing:
            self._throttle_pending[key] = (payload, existing[1])
            return
        async def _send_delayed():
            await asyncio.sleep(0.2)
            entry = self._throttle_pending.pop(key, None)
            if entry:
                final_payload, _ = entry
                if user_id is not None:
                    await self.send_to_student(user_id, final_payload)
        task = asyncio.create_task(_send_delayed())
        self._throttle_pending[key] = (payload, task)

    async def _broadcast_status(self):
        async with self._lock:
            online_user_ids = set(self.student_connections.keys())
        db = SessionLocal()
        try:
            all_users = db.query(User).filter(User.role == "user").all()
            total = len(all_users)
            online = [{"id": u.id, "username": u.username, "nickname": u.nickname}
                       for u in all_users if u.id in online_user_ids]
            offline = [{"id": u.id, "username": u.username, "nickname": u.nickname}
                        for u in all_users if u.id not in online_user_ids]
        finally:
            db.close()
        dead = set()
        for ws in list(self.admin_connections):
            try:
                await ws.send_json({
                    "type": "online_status", "online_count": len(online_user_ids),
                    "total_count": total, "online_users": online, "offline_users": offline,
                })
            except Exception:
                dead.add(ws)
        for d in dead:
            async with self._lock:
                self.admin_connections.discard(d)

    async def check_stale_connections(self, timeout: float = 60):
        while True:
            await asyncio.sleep(15)
            async with self._lock:
                now = time.time()
                stale = []
                for uid, conns in list(self.student_connections.items()):
                    alive = [(ws, h) for ws, h in conns if now - h < timeout]
                    dead_ws = [ws for ws, h in conns if now - h >= timeout]
                    if alive:
                        self.student_connections[uid] = alive
                    else:
                        stale.append(uid)
                        del self.student_connections[uid]
                    for ws in dead_ws:
                        try:
                            await ws.close()
                        except Exception:
                            pass
            if stale:
                await self._broadcast_status()

    async def disconnect_user(self, user_id: int):
        async with self._lock:
            if user_id in self.student_connections:
                conns = self.student_connections.pop(user_id)
                for ws, _ in conns:
                    try:
                        await ws.close(code=4005, reason="token invalidated")
                    except Exception:
                        pass
        self.auth_cache.invalidate(user_id)


manager = ConnectionManager()
