"""Database migration CLI with cross-platform file lock protection."""
import os
import sys
import time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
LOCK_FILE = DATA_DIR / ".migration.lock"


def _acquire_lock(timeout: float = 30.0):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Try portalocker
    try:
        import portalocker
        fd = open(LOCK_FILE, "w")
        deadline = time.monotonic() + timeout
        while True:
            try:
                portalocker.lock(fd, portalocker.LOCK_EX | portalocker.LOCK_NB)
                return fd
            except portalocker.exceptions.LockException:
                if time.monotonic() > deadline:
                    fd.close()
                    raise RuntimeError("无法获取迁移锁：超时")
                time.sleep(0.1)
    except ImportError:
        pass

    # Try fcntl (POSIX)
    try:
        import fcntl
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_RDWR)
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return os.fdopen(fd, "w")
            except BlockingIOError:
                if time.monotonic() > deadline:
                    os.close(fd)
                    raise RuntimeError("无法获取迁移锁：超时")
                time.sleep(0.1)
    except ImportError:
        pass

    # Try msvcrt (Windows)
    try:
        import msvcrt
        fd = open(LOCK_FILE, "w")
        deadline = time.monotonic() + timeout
        while True:
            try:
                msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
                return fd
            except OSError:
                if time.monotonic() > deadline:
                    fd.close()
                    raise RuntimeError("无法获取迁移锁：超时")
                time.sleep(0.1)
    except ImportError:
        raise RuntimeError("无可用文件锁实现：请安装 portalocker")


def _release_lock(lock_fd) -> None:
    try:
        lock_fd.close()
    except Exception:
        pass


def _parse_db_path() -> Path:
    """Extract filesystem path from sqlite:/// DATABASE_URL."""
    from backend.app.config import settings
    raw = settings.DATABASE_URL
    if raw.startswith("sqlite:///"):
        return Path(raw[len("sqlite:///"):])
    raise RuntimeError(f"不支持的 DATABASE_URL: {raw}")


def migrate_upgrade() -> None:
    from alembic import command
    from alembic.config import Config

    db_path = _parse_db_path()
    if not db_path.exists():
        print(f"错误: 数据库文件不存在: {db_path}")
        print("请先创建数据库（如通过 seed 命令）")
        sys.exit(1)

    print(f"数据库: {db_path}")
    lock_fd = _acquire_lock()
    try:
        alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
        print("迁移完成。")
    finally:
        _release_lock(lock_fd)


def migrate_status() -> None:
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    command.current(alembic_cfg)
    command.heads(alembic_cfg)


def migrate_downgrade(revision: str = "-1") -> None:
    from alembic import command
    from alembic.config import Config

    lock_fd = _acquire_lock()
    try:
        alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
        command.downgrade(alembic_cfg, revision)
        print(f"已回滚到: {revision}")
    finally:
        _release_lock(lock_fd)
