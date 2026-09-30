from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()

MAX_MPIN_FAILED_ATTEMPTS = 5
MPIN_LOCK_DURATION_MINUTES = 15


def hash_mpin(mpin: str) -> str:
    return password_hash.hash(mpin)


def verify_mpin(mpin: str, mpin_hash: str) -> bool:
    return password_hash.verify(mpin, mpin_hash)


def is_mpin_locked(mpin_locked_until: datetime | None) -> bool:
    if mpin_locked_until is None:
        return False

    now = datetime.now(timezone.utc)

    return now < mpin_locked_until


def get_mpin_lock_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        minutes=MPIN_LOCK_DURATION_MINUTES
    )