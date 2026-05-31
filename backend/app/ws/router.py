import json
from fastapi import WebSocket, WebSocketDisconnect
from backend.app.database import SessionLocal
from backend.app.services.auth_service import decode_token
from backend.app.models.user import User
from backend.app.ws.manager import manager


async def online_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    is_admin = False
    authenticated = False
    auth_token_version = None

    async def set_anonymous(reason: str | None = None):
        nonlocal user_id, is_admin, authenticated, auth_token_version
        if authenticated and user_id is not None:
            if is_admin:
                await manager.disconnect_admin(websocket)
            else:
                await manager.disconnect_student(websocket, user_id)
        user_id = None
        is_admin = False
        authenticated = False
        auth_token_version = None
        if reason:
            await websocket.send_json({"type": "auth_state", "status": "anonymous", "reason": reason})

    async def validate_authenticated_user() -> bool:
        nonlocal is_admin
        if not authenticated or user_id is None or auth_token_version is None:
            return False
        cached = manager.auth_cache.get(user_id)
        if cached is None:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user is None:
                    await set_anonymous("user_not_found")
                    return False
                manager.auth_cache.set(user_id, user.token_version, user.is_active, user.role)
                cached = (user.token_version, user.is_active, user.role)
            finally:
                db.close()
        current_tv, active, role = cached
        if not active or current_tv != auth_token_version:
            await set_anonymous("token_invalidated")
            return False
        if is_admin != (role == "admin"):
            await set_anonymous("role_changed")
            return False
        return True

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.close(code=4002, reason="invalid json")
                return

            msg_type = msg.get("type")
            if msg_type == "auth":
                token = msg.get("token")
                payload = decode_token(token) if token else None
                if payload is None or payload.get("type") != "access":
                    await set_anonymous("invalid_token")
                    continue
                uid_str = payload.get("sub")
                token_tv = payload.get("tv")
                if uid_str is None or token_tv is None:
                    await set_anonymous("invalid_token")
                    continue
                try:
                    next_user_id = int(uid_str)
                except (ValueError, TypeError):
                    await set_anonymous("invalid_token")
                    continue

                cached = manager.auth_cache.get(next_user_id)
                if cached is not None:
                    current_tv, active, role = cached
                    if token_tv != current_tv:
                        await set_anonymous("token_invalidated")
                        continue
                    if not active:
                        await set_anonymous("account_disabled")
                        continue
                else:
                    db = SessionLocal()
                    try:
                        user = db.query(User).filter(User.id == next_user_id).first()
                        if user is None:
                            await set_anonymous("user_not_found")
                            continue
                        manager.auth_cache.set(next_user_id, user.token_version, user.is_active, user.role)
                        current_tv, active, role = user.token_version, user.is_active, user.role
                        if token_tv != current_tv:
                            await set_anonymous("token_invalidated")
                            continue
                        if not active:
                            await set_anonymous("account_disabled")
                            continue
                    finally:
                        db.close()

                if authenticated:
                    await set_anonymous("reauth")
                user_id = next_user_id
                auth_token_version = token_tv
                is_admin = role == "admin"
                authenticated = True
                if is_admin:
                    await manager.connect_admin(websocket)
                else:
                    await manager.connect_student(websocket, user_id)
                await websocket.send_json({"type": "auth_state", "status": "authenticated", "role": role, "user_id": user_id})
                continue

            if msg_type in {"deauth", "logout"}:
                await set_anonymous("logout")
                continue

            if msg_type == "heartbeat":
                if authenticated and not is_admin and await validate_authenticated_user():
                    await manager.heartbeat(user_id)
                continue

            request_id = msg.get("request_id")
            if msg_type == "request_pvp_room_state":
                if authenticated and not is_admin and await validate_authenticated_user():
                    from backend.app.services.pvp_service import build_student_room_payload
                    try:
                        with SessionLocal() as db:
                            room_payload = build_student_room_payload(db, user_id)
                    except Exception:
                        import traceback
                        traceback.print_exc()
                        room_payload = None
                else:
                    room_payload = None
                await websocket.send_json({"type": "pvp_room_state", "room": room_payload, "request_id": request_id})
                continue

            if msg_type == "request_pvp_battle":
                if not authenticated or is_admin or not await validate_authenticated_user():
                    await websocket.send_json({"type": "pvp_error", "detail": "请先登录", "request_id": request_id})
                    continue
                from backend.app.services.pvp_service import build_pvp_battle_session_payload
                try:
                    with SessionLocal() as db:
                        try:
                            payload = build_pvp_battle_session_payload(db, user_id)
                        except LookupError as exc:
                            payload = {"type": "pvp_error", "detail": str(exc)}
                        except ValueError as exc:
                            payload = {"type": "pvp_error", "detail": str(exc)}
                except Exception:
                    import traceback
                    traceback.print_exc()
                    payload = {"type": "pvp_error", "detail": "服务端异常"}
                payload["request_id"] = request_id
                await websocket.send_json(payload)
                continue

            if msg_type == "request_pvp_rooms":
                if authenticated and is_admin and await validate_authenticated_user():
                    from backend.app.services.pvp_service import _load_admin_room_payloads
                    try:
                        with SessionLocal() as db:
                            rooms_payload = _load_admin_room_payloads(db)
                    except Exception:
                        import traceback
                        traceback.print_exc()
                        rooms_payload = []
                else:
                    rooms_payload = []
                await websocket.send_json({"type": "pvp_rooms", "rooms": rooms_payload, "request_id": request_id})
                continue

    except WebSocketDisconnect:
        if authenticated:
            await set_anonymous()
    except Exception:
        import traceback
        traceback.print_exc()
        try:
            if authenticated:
                await set_anonymous()
        except Exception:
            pass
