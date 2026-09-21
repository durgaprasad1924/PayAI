import secrets

from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def generate_otp() -> str:
    """
    Generate a secure 6-digit OTP.
    """

    otp = secrets.randbelow(900000) + 100000

    return str(otp)


def hash_otp(otp: str) -> str:
    """
    Hash the OTP before storing it in the database.
    """

    return password_hash.hash(otp)


def verify_otp(otp: str, otp_hash: str) -> bool:
    """
    Verify a user-provided OTP against the stored hash.
    """

    return password_hash.verify(otp, otp_hash)