from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.routers import achievements_router
from backend.app.services.achievement_service import build_achievement_wall


@achievements_router.get("/")
def list_achievements(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    result = build_achievement_wall(db, user.id)
    db.commit()
    return result
