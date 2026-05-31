import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from backend.app.database import Base, sessionmaker
from backend.app.routers import auth_router


@pytest.fixture
async def client(engine):
    """Test FastAPI app with :memory: DB"""
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")

    TestSessionLocal = sessionmaker(autoflush=False, bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from backend.app.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_register_and_login(client):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "newuser", "password": "test1234", "nickname": "New"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    resp = await client.post("/api/v1/auth/login", json={
        "username": "newuser", "password": "test1234"
    })
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_register_duplicate_username(client):
    await client.post("/api/v1/auth/register", json={
        "username": "dup", "password": "test1234", "nickname": "D"
    })
    resp = await client.post("/api/v1/auth/register", json={
        "username": "dup", "password": "test5678", "nickname": "D2"
    })
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "username": "wp", "password": "test1234", "nickname": "WP"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "wp", "password": "wrong"
    })
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_update_profile(client):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "profile_user", "password": "test1234", "nickname": "Before"
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = await client.put(
        "/api/v1/auth/profile",
        json={"nickname": "After"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "After"
