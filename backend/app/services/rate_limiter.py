import time

_request_log: dict[str, list[float]] = {}


def check_action_rate_limit(key: str, max_requests: int = 20, window_seconds: int = 60) -> bool:
    now = time.time()
    window = _request_log.get(key, [])
    pruned = [t for t in window if now - t < window_seconds]

    if not pruned:
        # Evict empty keys to prevent unbounded growth
        _request_log.pop(key, None)
    else:
        _request_log[key] = pruned

    if len(pruned) >= max_requests:
        return False
    pruned.append(now)
    _request_log[key] = pruned
    return True
