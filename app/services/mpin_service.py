from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_mpin(mpin: str) -> str:
    return password_hash.hash(mpin)


def verify_mpin(mpin: str, mpin_hash: str) -> bool:
    return password_hash.verify(mpin, mpin_hash)