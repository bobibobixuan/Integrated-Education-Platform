from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.deps import get_db, get_current_user
from backend.app.services.auth_service import (
    authenticate_user,
    register_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.models.user import User
from backend.app.models.record import UserStats
from backend.app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    PasswordChangeRequest,
    ProfileUpdateRequest,
)
from backend.app.routers import auth_router


@auth_router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

    user = register_user(db, body.username, body.password, body.nickname)
    stats = UserStats(user_id=user.id)
    db.add(stats)
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)}, token_version=user.token_version)
    refresh_token = create_refresh_token({"sub": str(user.id)}, token_version=user.token_version)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@auth_router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    access_token = create_access_token({"sub": str(user.id)}, token_version=user.token_version)
    refresh_token = create_refresh_token({"sub": str(user.id)}, token_version=user.token_version)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@auth_router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: LoginRequest, db: Session = Depends(get_db)):
    """Refresh tokens using a refresh_token in the password field (backward compat)."""
    payload = decode_token(body.password)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌")

    user_id_str = payload.get("sub")
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")

    token_tv = payload.get("tv")
    if token_tv is None or token_tv != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已失效，请重新登录")

    access_token = create_access_token({"sub": str(user.id)}, token_version=user.token_version)
    refresh_token = create_refresh_token({"sub": str(user.id)}, token_version=user.token_version)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@auth_router.put("/profile", response_model=UserResponse)
def update_profile(
    body: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    nickname = body.nickname.strip()
    if not nickname:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="昵称不能为空")

    user.nickname = nickname
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@auth_router.put("/password", response_model=TokenResponse)
def change_password(
    body: PasswordChangeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.force_password_change:
        if not body.old_password or not verify_password(body.old_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="旧密码错误")

    user.password_hash = hash_password(body.new_password)
    user.force_password_change = False
    db.execute(
        text("UPDATE users SET token_version = token_version + 1 WHERE id = :id"),
        {"id": user.id},
    )
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)}, token_version=user.token_version)
    refresh_token = create_refresh_token({"sub": str(user.id)}, token_version=user.token_version)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )
