from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["auth"])
units_router = APIRouter(prefix="/units", tags=["units"])
questions_router = APIRouter(prefix="/questions", tags=["questions"])
records_router = APIRouter(prefix="/records", tags=["records"])
scores_router = APIRouter(prefix="/scores", tags=["scores"])
achievements_router = APIRouter(prefix="/achievements", tags=["achievements"])
leaderboard_router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])
pvp_router = APIRouter(prefix="/pvp", tags=["pvp"])

from backend.app.routers import auth as _auth           # noqa: F401
from backend.app.routers import units as _units          # noqa: F401
from backend.app.routers import questions as _questions  # noqa: F401
from backend.app.routers import records as _records      # noqa: F401
from backend.app.routers import scores as _scores        # noqa: F401
from backend.app.routers import achievements as _achievements  # noqa: F401
from backend.app.routers import leaderboard as _leaderboard   # noqa: F401
from backend.app.routers import admin as _admin          # noqa: F401
from backend.app.routers import pvp as _pvp              # noqa: F401
