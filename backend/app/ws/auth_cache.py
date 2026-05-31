import time


class AuthCache:
    def __init__(self):
        self._cache: dict[int, tuple[int, bool, str, float]] = {}

    def get(self, user_id: int) -> tuple[int, bool, str] | None:
        entry = self._cache.get(user_id)
        if entry is None:
            return None
        tv, active, role, ts = entry
        if time.time() - ts > 10:
            del self._cache[user_id]
            return None
        return (tv, active, role)

    def set(self, user_id: int, token_version: int, is_active: bool, role: str):
        self._cache[user_id] = (token_version, is_active, role, time.time())

    def invalidate(self, user_id: int):
        self._cache.pop(user_id, None)
